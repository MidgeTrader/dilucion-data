export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

  try {
    const { question, ticker, url, prompt_type, use_reasoning } = req.body;

    if (!question && !prompt_type) {
      return res.status(400).json({ error: 'question or prompt_type is required' });
    }

    const response = await fetch(`${backendUrl}/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question || '',
        ticker: ticker || null,
        url: url || null,
        prompt_type: prompt_type || null,
        use_reasoning: use_reasoning || false,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: data.detail || data.error || 'Backend RAG error',
      });
    }

    return res.status(200).json(data);
  } catch (err) {
    console.error('RAG proxy error:', err);
    return res.status(503).json({
      error: `Backend unavailable at ${backendUrl}. Start with: python main.py serve`,
    });
  }
}
