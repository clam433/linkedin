import { useState } from "react";
import axios from "axios";
import type { CollectResponse, ScrapedRow, ApiError } from "./types";

function App() {
  const API_BASE = import.meta.env.VITE_API_BASE_URL;
  const [htmlContent, setHtmlContent] = useState("");
  const [results, setResults] = useState<ScrapedRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [count, setCount] = useState(0);

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    setResults([]);
    setCount(0);


    try {
      const response = await axios.post<CollectResponse>(
        `${API_BASE}/api/collect`,
        { html_content: htmlContent },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      setResults(response.data.results);
      setCount(response.data.count);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as ApiError | undefined;
        setError(data?.message || "Something went wrong.");
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setHtmlContent("");
    setResults([]);
    setCount(0);
    setError("");
  };

  const handleCopy = async () => {
    if (results.length === 0) return;

    const header = ["Name", "Role", "Location"];
    const rows = results.map((row) => [row.name, row.role, row.location]);
    const text = [header, ...rows].map((r) => r.join("\t")).join("\n");

    try {
      await navigator.clipboard.writeText(text);
      alert("Table copied to clipboard!");
    } catch {
      alert("Failed to copy table.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 px-4 py-10">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-8 text-center text-4xl font-bold">
          Name Collector
        </h1>

        <div className="rounded-xl bg-white p-6 shadow">
          <label className="mb-3 block text-lg font-medium">
            Enter LinkedIn HTML content
          </label>

          <textarea
            value={htmlContent}
            onChange={(e) => setHtmlContent(e.target.value)}
            rows={16}
            className="w-full rounded-lg border border-gray-300 p-4 outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Paste LinkedIn HTML here..."
          />

          <div className="mt-4 flex flex-wrap gap-3">
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="rounded-lg border border-black px-5 py-2 text-base hover:bg-cyan-100 disabled:opacity-50"
            >
              {loading ? "Processing..." : "Submit"}
            </button>

            <button
              onClick={handleClear}
              className="rounded-lg border border-black px-5 py-2 text-base hover:bg-gray-200"
            >
              Clear Content
            </button>

            <button
              onClick={handleCopy}
              disabled={results.length === 0}
              className="rounded-lg bg-green-600 px-5 py-2 text-base text-white hover:bg-green-700 disabled:opacity-50"
            >
              Copy to Clipboard
            </button>
          </div>

          {error && (
            <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-red-700">
              {error}
            </div>
          )}
        </div>

        <div className="mt-8 rounded-xl bg-white p-6 shadow">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">Results</h2>
            <span className="text-sm text-gray-600">{count} result(s)</span>
          </div>

          {results.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-black">
                <thead>
                  <tr className="bg-gray-200">
                    <th className="border border-black px-4 py-3 text-left text-lg">
                      Name
                    </th>
                    <th className="border border-black px-4 py-3 text-left text-lg">
                      Role
                    </th>
                    <th className="border border-black px-4 py-3 text-left text-lg">
                      Location
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((row, index) => (
                    <tr key={`${row.name}-${index}`}>
                      <td className="border border-black px-4 py-3">{row.name}</td>
                      <td className="border border-black px-4 py-3">{row.role}</td>
                      <td className="border border-black px-4 py-3">{row.location}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            !loading && (
              <div className="text-center text-lg text-gray-600">
                No results found.
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

export default App;