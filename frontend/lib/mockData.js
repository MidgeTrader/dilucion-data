/** Demo/mock data for UI preview without backend. */

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';

export const mockTopDilution = [
  { ticker: 'SPHL', cik: '1842568', form_type: 'S-3', dilution_percentage: 32.5, warrants_found: true, has_atm: true, has_full_ratchet: false, has_prefunded_warrants: true, risk_level: 'HIGH', filed_date: '2026-06-15', source_url: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SPHL' },
  { ticker: 'MULN', cik: '1499968', form_type: '424B5', dilution_percentage: 28.1, warrants_found: true, has_atm: false, has_full_ratchet: true, has_prefunded_warrants: false, risk_level: 'HIGH', filed_date: '2026-06-12' },
  { ticker: 'FFIE', cik: '1805521', form_type: 'S-3/A', dilution_percentage: 24.7, warrants_found: false, has_atm: true, has_full_ratchet: false, has_prefunded_warrants: false, risk_level: 'HIGH', filed_date: '2026-06-10' },
  { ticker: 'SINT', cik: '1269026', form_type: '8-K', dilution_percentage: 18.3, warrants_found: true, has_atm: false, has_full_ratchet: false, has_prefunded_warrants: true, risk_level: 'MEDIUM', filed_date: '2026-06-08' },
  { ticker: 'NKLA', cik: '1731289', form_type: '424B5', dilution_percentage: 15.2, warrants_found: true, has_atm: true, has_full_ratchet: false, has_prefunded_warrants: false, risk_level: 'MEDIUM', filed_date: '2026-06-05' },
  { ticker: 'ATER', cik: '1756594', form_type: 'S-3', dilution_percentage: 12.8, warrants_found: false, has_atm: true, has_full_ratchet: false, has_prefunded_warrants: false, risk_level: 'MEDIUM', filed_date: '2026-06-01' },
  { ticker: 'BBAI', cik: '1838163', form_type: '10-Q', dilution_percentage: 8.4, warrants_found: true, has_atm: false, has_full_ratchet: false, has_prefunded_warrants: false, risk_level: 'LOW', filed_date: '2026-05-28' },
  { ticker: 'AAPL', cik: '320193', form_type: '10-K', dilution_percentage: 2.1, warrants_found: false, has_atm: false, has_full_ratchet: false, has_prefunded_warrants: false, risk_level: 'LOW', filed_date: '2026-05-20' },
];

export const mockAlerts = mockTopDilution.slice(0, 6).map((r) => ({
  ...r,
  accession_number: `0001104659-26-${Math.floor(Math.random() * 900000 + 100000)}`,
  shelf_amount_usd: r.dilution_percentage * 800000,
  source_url: r.source_url || 'https://www.sec.gov/',
}));

export const mockFilings = mockTopDilution.map((r, i) => ({
  accession_number: `0001104659-26-${100000 + i}`,
  cik: r.cik,
  ticker: r.ticker,
  form_type: r.form_type,
  filed_date: r.filed_date,
  title: `${r.form_type} — ${r.ticker} Shelf Registration / Prospectus Supplement`,
  shelf_amount_usd: 25000000 - i * 2000000,
  dilution_percentage: r.dilution_percentage,
  warrants_found: r.warrants_found,
  has_atm: r.has_atm,
  has_full_ratchet: r.has_full_ratchet,
  has_prefunded_warrants: r.has_prefunded_warrants,
  summary: `Demo: ${r.form_type} detected with ${r.dilution_percentage}% estimated dilution. ATM and warrant clauses flagged for review.`,
  source_url: 'https://www.sec.gov/cgi-bin/browse-edgar',
}));

const mockArticlesByTicker = {
  SPHL: [
    { title: 'Springview Holdings announces retail expansion in Southeast Asia', source: 'MT Newswires', date: '2026-06-14', url: '#' },
    { title: 'Small-cap retail names draw attention amid sector rotation', source: 'Seeking Alpha', date: '2026-06-10', url: '#' },
    { title: 'SPHL: Shelf filing raises dilution concerns for micro-cap holders', source: 'Dilution Tracker', date: '2026-06-08', url: '#' },
    { title: 'NASDAQ micro-caps with high borrow rates face squeeze risk', source: 'Benzinga', date: '2026-06-05', url: '#' },
    { title: 'Consumer cyclical sector sees renewed interest from retail traders', source: 'MarketWatch', date: '2026-06-01', url: '#' },
  ],
};

const extraFilingsByTicker = {
  SPHL: [
    { accession_number: '0001104659-26-100001', form_type: 'S-3', filed_date: '2026-06-15', title: 'Registration Statement — Shelf Offering up to $50M', shelf_amount_usd: 50000000, dilution_percentage: 32.5, warrants_found: true, has_atm: true, has_full_ratchet: false, has_prefunded_warrants: true, summary: 'Universal shelf registration filed. ATM provision detected. Prefunded warrants included.', source_url: 'https://www.sec.gov/' },
    { accession_number: '0001104659-26-100002', form_type: '424B5', filed_date: '2026-05-28', title: 'Prospectus Supplement — $8.5M Registered Direct Offering', shelf_amount_usd: 8500000, dilution_percentage: 18.2, warrants_found: true, has_atm: false, has_full_ratchet: false, has_prefunded_warrants: true, summary: 'Registered direct offering with prefunded warrants at $2.10 exercise.', source_url: 'https://www.sec.gov/' },
    { accession_number: '0001104659-26-100003', form_type: '8-K', filed_date: '2026-05-20', title: 'Current Report — Material Definitive Agreement', shelf_amount_usd: null, dilution_percentage: null, warrants_found: false, has_atm: false, has_full_ratchet: false, has_prefunded_warrants: false, summary: '8-K disclosing strategic partnership and potential equity issuance.', source_url: 'https://www.sec.gov/' },
    { accession_number: '0001104659-26-100004', form_type: '10-Q', filed_date: '2026-05-15', title: 'Quarterly Report — Q1 2026', shelf_amount_usd: null, dilution_percentage: 2.1, warrants_found: false, has_atm: false, has_full_ratchet: false, has_prefunded_warrants: false, summary: 'Quarterly financials. Cash runway approximately 4 months at current burn.', source_url: 'https://www.sec.gov/' },
    { accession_number: '0001104659-26-100005', form_type: 'S-3/A', filed_date: '2026-04-10', title: 'Amendment No. 1 to Shelf Registration', shelf_amount_usd: 50000000, dilution_percentage: 30.0, warrants_found: true, has_atm: true, has_full_ratchet: false, has_prefunded_warrants: false, summary: 'Amended shelf increases ATM capacity. Warrant overhang noted.', source_url: 'https://www.sec.gov/' },
    { accession_number: '0001104659-26-100006', form_type: '424B5', filed_date: '2026-03-22', title: 'Prospectus Supplement — $5M PIPE Transaction', shelf_amount_usd: 5000000, dilution_percentage: 12.4, warrants_found: true, has_atm: false, has_full_ratchet: true, has_prefunded_warrants: false, summary: 'PIPE with full ratchet anti-dilution provision flagged as HIGH risk.', source_url: 'https://www.sec.gov/' },
  ],
};

function mockDilutionDetail(ticker, base, profile) {
  const pct = base.dilution_percentage || 15;
  return {
    estimated_dilution_pct: pct,
    risk_level: base.risk_level || (pct >= 20 ? 'HIGH' : pct >= 10 ? 'MEDIUM' : 'LOW'),
    shelf: {
      active: true,
      capacity_usd: 50000000,
      remaining_usd: 32500000,
      expiration: '2028-06-15',
    },
    atm: {
      active: base.has_atm,
      capacity_usd: 15000000,
      used_usd: 4200000,
      agent: 'Maxim Group LLC',
    },
    warrants: [
      { type: 'Prefunded', count: 850000, exercise_price: 0.01, expiration: '2029-03-22', in_the_money: true },
      { type: 'Series A', count: 425000, exercise_price: 2.75, expiration: '2028-06-15', in_the_money: false },
      { type: 'Placement', count: 212500, exercise_price: 3.25, expiration: '2027-12-31', in_the_money: false },
    ],
    flags: {
      warrants_found: base.warrants_found,
      has_atm: base.has_atm,
      has_full_ratchet: base.has_full_ratchet,
      has_prefunded_warrants: base.has_prefunded_warrants,
    },
    events: [
      { date: '2026-06-15', type: 'S-3', description: 'New $50M shelf registration filed', impact_pct: 32.5 },
      { date: '2026-05-28', type: '424B5', description: '$8.5M registered direct + prefunded warrants', impact_pct: 18.2 },
      { date: '2026-03-22', type: '424B5', description: '$5M PIPE with full ratchet anti-dilution', impact_pct: 12.4 },
      { date: '2026-01-10', type: '8-K', description: 'Reverse split 1:20 effective', impact_pct: null },
    ],
    share_structure: {
      float: profile.float_shares,
      outstanding: profile.shares_outstanding,
      fully_diluted: Math.round(profile.shares_outstanding * 1.35),
      cash_months: 4,
    },
  };
}

function mockInsights(ticker, base) {
  return [
    {
      id: 1,
      category: 'Dilution Risk',
      severity: 'high',
      title: 'Active $50M shelf with ATM provision',
      body: `${ticker} filed an S-3 shelf registration for up to $50M with an at-the-market (ATM) offering provision. Based on current float of ~1.26M shares, full utilization could dilute existing holders by ~32%.`,
      source_form: 'S-3',
      date: '2026-06-15',
    },
    {
      id: 2,
      category: 'Warrants',
      severity: 'medium',
      title: '850K prefunded warrants outstanding',
      body: 'Prefunded warrants with $0.01 exercise price are effectively common stock. Combined with Series A warrants, total warrant overhang represents ~100% of current float.',
      source_form: '424B5',
      date: '2026-05-28',
    },
    {
      id: 3,
      category: 'Cash Runway',
      severity: 'medium',
      title: 'Limited cash runway (~4 months)',
      body: 'Latest 10-Q indicates cash per share of $0.30 with quarterly burn rate suggesting capital raise likely within next 2 quarters.',
      source_form: '10-Q',
      date: '2026-05-15',
    },
    {
      id: 4,
      category: 'Short Interest',
      severity: 'high',
      title: 'Elevated borrow rate signals squeeze potential',
      body: `Borrow rate of ${ticker === 'SPHL' ? '459%' : '18.5%'} with ${ticker === 'SPHL' ? '23.7%' : '12.3%'} short float suggests significant cost to maintain short positions.`,
      source_form: 'Market Data',
      date: '2026-06-18',
    },
    {
      id: 5,
      category: 'Anti-Dilution',
      severity: 'high',
      title: 'Full ratchet provision in March PIPE',
      body: 'March 2026 PIPE included full ratchet anti-dilution, meaning future offerings below PIPE price trigger additional share issuance to PIPE investors.',
      source_form: '424B5',
      date: '2026-03-22',
    },
  ];
}

function mockTranscripts(ticker) {
  return [
    { id: 1, quarter: 'Q1 2026', date: '2026-05-22', title: `${ticker} Q1 2026 Earnings Call`, duration: '32 min', highlights: ['Revenue up 12% YoY', 'Expanded Southeast Asia footprint', 'Cash management discussed'] },
    { id: 2, quarter: 'Q4 2025', date: '2026-03-10', title: `${ticker} Q4 2025 Earnings Call`, duration: '28 min', highlights: ['Full year results', 'Store count: 3 locations', 'Guidance for 2026'] },
    { id: 3, quarter: 'Q3 2025', date: '2025-11-15', title: `${ticker} Q3 2025 Earnings Call`, duration: '25 min', highlights: ['Seasonal trends', 'Inventory management', 'Cost reduction initiatives'] },
  ];
}

function generateCandles(basePrice = 5.35, days = 90) {
  const candles = [];
  let price = basePrice * 1.35;
  const start = new Date();
  start.setDate(start.getDate() - days);
  let idx = 0;
  for (let i = 0; i < days; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    const drift = idx / 60;
    const change = (Math.random() - 0.52 + drift * 0.02) * 0.06;
    const open = price;
    let close = Math.max(0.5, price * (1 + change));
    if (idx >= 58) close = basePrice + (Math.random() - 0.5) * 0.08;
    const high = Math.max(open, close) * (1 + Math.random() * 0.025);
    const low = Math.min(open, close) * (1 - Math.random() * 0.025);
    candles.push({
      date: d.toISOString().slice(0, 10),
      open: +open.toFixed(2),
      high: +high.toFixed(2),
      low: +low.toFixed(2),
      close: +close.toFixed(2),
      volume: Math.floor(Math.random() * 3000000 + 400000),
    });
    price = close;
    idx += 1;
  }
  return candles;
}

export function mockTickerData(ticker = 'SPHL') {
  const t = ticker.toUpperCase();
  const isSphl = t === 'SPHL';
  const base = mockTopDilution.find((x) => x.ticker === t) || mockTopDilution[0];
  const dilution = base.dilution_percentage || 15;

  const sphlDescription =
    'Springview Holdings Ltd is a Singapore-based holding company. Through its subsidiaries, the company operates department stores and retail distribution channels across Southeast Asia. The company focuses on consumer cyclical retail with exposure to discretionary spending trends in the region.';

  const profile = {
    ticker: t,
    cik: base.cik,
    company_name: isSphl
      ? 'Springview Holdings Ltd Class A Ordinary Shares'
      : `${t} Holdings Inc.`,
    sector: isSphl ? 'Consumer Cyclical' : 'Healthcare Equipment',
    industry: isSphl ? 'Residential Construction' : 'Medical Devices',
    country: isSphl ? 'SG' : 'US',
    exchange: isSphl ? 'NASDAQ Global Select' : 'NYSE',
    website: isSphl ? 'springview.com' : `${t.toLowerCase()}.com`,
    employees: isSphl ? 11 : 240,
    float_shares: isSphl ? 1260000 : 4200000,
    shares_outstanding: isSphl ? 12420000 : 8500000,
    market_cap: isSphl ? 31430000 : 85000000,
    enterprise_value: isSphl ? 27910000 : 92000000,
    price: isSphl ? 2.53 : 5.35,
    change_percent: isSphl ? -1.2 : 2.34,
    borrow_rate: isSphl ? 459.1697 : 18.5,
    short_percent_float: isSphl ? 0.9 : 12.3,
    days_to_cover: isSphl ? 1.74 : 2.1,
    cash_per_share: isSphl ? 0.19 : 1.2,
    avg_volume: isSphl ? 710760 : 2400000,
    institutional_ownership: isSphl ? 0 : 18.5,
    description: sphlDescription,
    about: sphlDescription,
  };

  const allFilings = (extraFilingsByTicker[t] || extraFilingsByTicker.SPHL).map((f) => ({ ...f, ticker: t, cik: base.cik }));

  return {
    profile,
    filings: allFilings,
    articles: mockArticlesByTicker[t] || mockArticlesByTicker.SPHL.map((a) => ({ ...a, title: a.title.replace('SPHL', t) })),
    news: mockArticlesByTicker[t] || mockArticlesByTicker.SPHL.map((a) => ({ ...a, title: a.title.replace('SPHL', t) })),
    insights: mockInsights(t, base),
    dilution: mockDilutionDetail(t, base, profile),
    transcripts: mockTranscripts(t),
    earnings: {
      next: { date: '2026-08-15', estimate: '-0.12' },
      last: { date: '2026-05-20', eps: '-0.08', surprise: -5.2 },
    },
    candles: generateCandles(isSphl ? 2.53 : 12.5, 90),
    risk: {
      offering_ability: isSphl ? 'Low' : dilution >= 20 ? 'High' : 'Med',
      offering_frequency: isSphl ? 'Low' : 'Low',
      dilution: isSphl ? 'Low' : dilution >= 20 ? 'High' : dilution >= 10 ? 'Med' : 'Low',
      cash_need: isSphl ? 'Med' : 'High',
      overall_offering_risk: isSphl ? 'Low' : dilution >= 20 ? 'High' : 'Med',
      warrant_exercise: isSphl ? 'Low' : base.warrants_found ? 'High' : 'Low',
    },
  };
}

export const mockSearchResults = mockTopDilution.map((r) => ({
  ticker: r.ticker,
  cik: r.cik,
  company_name: r.ticker === 'SPHL'
    ? 'Springview Holdings Ltd Class A Ordinary Shares'
    : `${r.ticker} Holdings Inc.`,
}));

export async function fetchTopDilution(limit = 15) {
  if (DEMO_MODE) return mockTopDilution.slice(0, limit);
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const r = await fetch(`${backend}/dilution/top?limit=${limit}`);
  if (!r.ok) throw new Error('Failed to load dilution data');
  return r.json();
}

export async function fetchAlertsFeed(limit = 10) {
  if (DEMO_MODE) return mockAlerts.slice(0, limit);
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const r = await fetch(`${backend}/alerts/feed?limit=${limit}`);
  if (!r.ok) throw new Error('Failed to load alerts');
  return r.json();
}

export async function fetchAllFilings(limit = 100) {
  if (DEMO_MODE) return mockFilings.slice(0, limit);
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const r = await fetch(`${backend}/filings/all?limit=${limit}`);
  if (!r.ok) throw new Error('Failed to load filings');
  return r.json();
}

export async function fetchTickerNews(ticker, limit = 20) {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const r = await fetch(`${backend}/ticker/${ticker.toUpperCase()}/news?limit=${limit}`);
  if (!r.ok) throw new Error(`Failed to load news for ${ticker}`);
  return r.json();
}

export async function fetchTicker(ticker) {
  if (DEMO_MODE) return mockTickerData(ticker);
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const r = await fetch(`${backend}/ticker/${ticker.toUpperCase()}`);
  if (!r.ok) throw new Error(`Failed to load ${ticker}`);
  const data = await r.json();
  // Normaliza news/articles para el frontend
  const news = data.news || data.articles || [];
  return { ...data, news, articles: data.articles || news };
}

export async function searchTickers(q, limit = 8) {
  if (DEMO_MODE) {
    const u = q.toUpperCase();
    return mockSearchResults.filter(
      (x) => x.ticker.includes(u) || x.company_name.toUpperCase().includes(u)
    ).slice(0, limit);
  }
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const r = await fetch(`${backend}/search?q=${encodeURIComponent(q)}&limit=${limit}`);
  if (!r.ok) throw new Error('Search failed');
  return r.json();
}
