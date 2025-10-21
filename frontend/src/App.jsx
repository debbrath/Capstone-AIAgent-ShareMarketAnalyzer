import { useState } from "react";

function App(){
  const [url, setUrl] = useState("");
  const [symbol, setSymbol] = useState("");
  const [result, setResult] = useState(null);

  async function handlePredict(e){
    e.preventDefault();
    const body = { source_url: url || null, symbol: symbol || null, horizon_days: 30 };
    const res = await fetch("/api/predict", {
      method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)
    });
    const json = await res.json();
    setResult(json);
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold">Upper/Lower Predictor</h1>
      <form onSubmit={handlePredict}>
        <input value={url} onChange={e=>setUrl(e.target.value)} placeholder="Company URL (biniyog...)" className="border p-2 m-2" />
        <input value={symbol} onChange={e=>setSymbol(e.target.value)} placeholder="Symbol (optional)" className="border p-2 m-2" />
        <button className="bg-blue-600 text-white px-4 py-2 rounded">Predict</button>
      </form>

      {result && (
        <div className="mt-6 p-4 border rounded">
          <h2>Results</h2>
          <p>Lower: {result.lower_limit}</p>
          <p>Upper: {result.upper_limit}</p>
          <p>Confidence: {result.confidence}</p>
          <details>
            <summary>Explanation & Sources</summary>
            <pre>{result.explanation}</pre>
            <ul>
              {result.sources.map(s => <li key={s}><a href={s} target="_blank" rel="noreferrer">{s}</a></li>)}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}

export default App;