// netlify/server/index.mjs — Netlify deployment of the EduSimplify /simplify API.
//
// This mirrors app.py, prompts.py and watsonx_client.py (used for local Flask
// development). Keep SECTION_LABELS and the prompt in sync with prompts.py.

export const config = { path: '/simplify' }

const IAM_TOKEN_URL = 'https://iam.cloud.ibm.com/identity/token'
const REQUEST_TIMEOUT_MS = 60_000
const MAX_SECTION_CHARS = 1200
const VALID_LEVELS = ['beginner', 'intermediate', 'expert']

const LEVEL_DESCRIPTIONS = {
  beginner:
    'a complete beginner with no prior knowledge. ' +
    'Use very simple words, short sentences, and friendly analogies.',
  intermediate:
    'someone with basic familiarity with the subject. ' +
    'Use clear explanations and introduce technical terms with brief definitions.',
  expert:
    'an advanced learner or professional. ' +
    'Use precise technical language, depth, and nuance, but remain concise.',
}

const SECTION_LABELS = [
  'Simplified Explanation',
  'Key Concepts',
  'Real-world Analogy',
  'Example',
  'Important Terms',
  'Quick Revision',
  'Quiz Questions',
]

class ConfigError extends Error {}

function getRequiredEnv(name, fallback) {
  const value = (process.env[name] || fallback || '').trim()
  if (!value) {
    throw new ConfigError(
      `Required environment variable '${name}' is not set. ` +
        'Add it in the Netlify project settings under Environment variables.',
    )
  }
  return value
}

function buildPrompt(topic, level) {
  const audience = LEVEL_DESCRIPTIONS[level]
  return (
    `You are an expert educator. Explain the following topic for ${audience}\n\n` +
    `TOPIC: ${topic}\n\n` +
    'IMPORTANT OUTPUT RULES:\n' +
    'Generate exactly 7 sections using the exact headings below. ' +
    'Each heading must appear exactly as written, on its own line, followed by a colon. ' +
    'Do not use labels such as S1, S2, S3, S4, S5, S6, S7, [S1], [S2], ' +
    'or any other section labels. ' +
    'Do not omit any section. ' +
    'Do not add extra sections. ' +
    'Do not add an introduction before the first heading or commentary after the final section.\n\n' +
    'REQUIRED HEADINGS IN THIS EXACT ORDER:\n' +
    '1. Simplified Explanation:\n' +
    '2. Key Concepts:\n' +
    '3. Real-world Analogy:\n' +
    '4. Example:\n' +
    '5. Important Terms:\n' +
    '6. Quick Revision:\n' +
    '7. Quiz Questions:\n\n' +
    'CONTENT REQUIREMENTS:\n' +
    'Simplified Explanation: 2-4 concise sentences. Stay strictly on-topic.\n' +
    'Key Concepts: exactly 3-5 short bullet points, each starting with a dash.\n' +
    'Real-world Analogy: exactly 1 relatable sentence.\n' +
    'Example: 1-3 concrete, topic-specific sentences.\n' +
    'Important Terms: exactly 4-6 relevant terms. ' +
    "Format each as 'Term: definition.' " +
    'Do not include unrelated terms or extra prose.\n' +
    'Quick Revision: exactly 3-5 short bullet points, each starting with a dash.\n' +
    'Quiz Questions: exactly 3 multiple-choice questions. ' +
    'Each question must have four options A), B), C), D) ' +
    'and one Answer line.\n\n' +
    'For Expert level, use technically accurate and precise language, ' +
    'but remain concise. ' +
    'Never produce filler, unrelated content, invented sections, ' +
    'or placeholder text.\n\n' +
    'Begin your response immediately with the first required section and ' +
    'place its content on the following line.\n'
  )
}

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\-]/g, '\\$&')
const LABEL_PATTERN = SECTION_LABELS.map(escapeRe).join('|')
const PREFIX = String.raw`^\*{0,2}(?:#{1,3}\s*)?(?:\d+\.\s*)?(` + LABEL_PATTERN + ')'

function resolveLabel(text) {
  const t = text.trim().toLowerCase()
  return SECTION_LABELS.find((l) => l.toLowerCase() === t) || null
}

function parseSections(rawText) {
  const result = Object.fromEntries(SECTION_LABELS.map((l) => [l, 'Not available.']))
  const lineHeadingRe = new RegExp(PREFIX + String.raw`\*{0,2}\s*:?\*{0,2}\s*$`, 'gim')
  const startHeadingRe = new RegExp(PREFIX + String.raw`\*{0,2}\s*:?\*{0,2}\s*\n`, 'i')

  const all = [] // [start, end, label]
  const m0 = startHeadingRe.exec(rawText)
  if (m0 && m0.index === 0) {
    const label = resolveLabel(m0[1])
    if (label) all.push([0, m0[0].length, label])
  }
  const start0Captured = all.length > 0

  for (const m of rawText.matchAll(lineHeadingRe)) {
    if (start0Captured && m.index === 0) continue
    const label = resolveLabel(m[1])
    if (label && (all.length === 0 || all[all.length - 1][0] !== m.index)) {
      all.push([m.index, m.index + m[0].length, label])
    }
  }

  if (all.length === 0) {
    result[SECTION_LABELS[0]] = rawText.trim()
    return result
  }

  const seen = new Set()
  all.forEach(([, end, label], idx) => {
    if (seen.has(label)) return
    seen.add(label)
    const next = idx + 1 < all.length ? all[idx + 1][0] : rawText.length
    const content = rawText.slice(end, next).trim()
    if (content) result[label] = content.slice(0, MAX_SECTION_CHARS)
  })
  return result
}

async function fetchWithTimeout(url, options, timeoutMessage) {
  try {
    return await fetch(url, { ...options, signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS) })
  } catch (err) {
    if (err.name === 'TimeoutError') throw new Error(timeoutMessage)
    throw new Error(`Network error: ${err.message}`)
  }
}

async function getIamToken(apiKey) {
  const res = await fetchWithTimeout(
    IAM_TOKEN_URL,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'urn:ibm:params:oauth:grant-type:apikey',
        apikey: apiKey,
      }),
    },
    'Timed out while connecting to IBM IAM.',
  )
  if (!res.ok) throw new Error(`IBM IAM authentication failed (HTTP ${res.status}).`)
  const data = await res.json()
  if (!data.access_token) {
    throw new Error('IBM IAM returned no access_token. Check that your API key is valid.')
  }
  return data.access_token
}

async function generate(prompt) {
  const apiKey = getRequiredEnv('WATSONX_API_KEY')
  const projectId = getRequiredEnv('WATSONX_PROJECT_ID')
  const baseUrl = getRequiredEnv('WATSONX_URL', 'https://us-south.ml.cloud.ibm.com').replace(/\/+$/, '')
  const modelId = getRequiredEnv('WATSONX_MODEL_ID', 'ibm/granite-4-h-small')

  const token = await getIamToken(apiKey)

  const res = await fetchWithTimeout(
    `${baseUrl}/ml/v1/text/generation?version=2023-05-29`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        model_id: modelId,
        project_id: projectId,
        input: prompt,
        parameters: { decoding_method: 'greedy', max_new_tokens: 2000, repetition_penalty: 1.1 },
      }),
    },
    'The request to IBM watsonx.ai timed out. The model may be busy — please try again.',
  )

  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const msg = data?.errors?.[0]?.message || `HTTP ${res.status}`
    throw new Error(`IBM watsonx.ai API error: ${msg}`)
  }
  const text = data?.results?.[0]?.generated_text
  if (typeof text !== 'string') throw new Error('Unexpected response format from IBM watsonx.ai.')
  if (!text.trim()) {
    throw new Error(
      'IBM watsonx.ai returned an empty response. Try rephrasing your topic or selecting a different level.',
    )
  }
  return text.trim()
}

const json = (body, status) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

export default async function handler(request) {
  if (request.method !== 'POST') {
    return json({ success: false, error: 'Method not allowed.' }, 405)
  }

  const data = await request.json().catch(() => null)
  if (!data || typeof data !== 'object') {
    return json({ success: false, error: 'Request body must be JSON.' }, 400)
  }

  const topic = String(data.topic ?? '').trim()
  const level = String(data.level ?? '').trim().toLowerCase()

  if (!topic) return json({ success: false, error: 'Please enter a topic.' }, 400)
  if (topic.length > 2000) {
    return json(
      { success: false, error: 'Topic is too long. Please keep it under 2000 characters.' },
      400,
    )
  }
  if (!VALID_LEVELS.includes(level)) {
    return json({ success: false, error: `Level must be one of: ${VALID_LEVELS.join(', ')}.` }, 400)
  }

  // The model can take longer than the platform's 20s time-to-first-byte limit,
  // so the response starts immediately and sends whitespace keep-alives (valid
  // leading JSON whitespace) until the final JSON body is ready. The frontend
  // checks `data.success`, so errors are still reported correctly.
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      const keepAlive = setInterval(() => controller.enqueue(encoder.encode(' ')), 5000)
      let body
      try {
        const rawText = await generate(buildPrompt(topic, level))
        body = { success: true, sections: parseSections(rawText) }
      } catch (err) {
        console.error('simplify error:', err.message)
        body = { success: false, error: err.message }
      } finally {
        clearInterval(keepAlive)
      }
      controller.enqueue(encoder.encode(JSON.stringify(body)))
      controller.close()
    },
  })

  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  })
}
