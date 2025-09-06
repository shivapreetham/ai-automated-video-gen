"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [topic, setTopic] = useState("science facts");
  const [duration, setDuration] = useState(30);
  const [voice, setVoice] = useState("default");
  const [runId, setRunId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setRunId("");
    try {
      const res = await fetch("http://localhost:3000/generate-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          topic, 
          style: "informative",
          num_segments: Math.ceil(Number(duration) / 6),
          language: "en"
        }),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      const id = data.job_id ?? "";
      setRunId(id);
      if (id) {
        router.push(`/run/${id}`);
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "2rem auto", padding: 24 }}>
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <h1 style={{ fontSize: 32, fontWeight: "bold", marginBottom: 8 }}>AI Video Generator</h1>
        <p style={{ color: "#6b7280", fontSize: 18 }}>
          Create engaging videos with AI-powered script writing and voiceovers
        </p>
      </div>
      
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 20 }}>
        <div>
          <label style={{ display: "block", fontWeight: "500", marginBottom: 8 }}>
            Video Description
          </label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Describe what you want your video to be about (e.g., 'Explain quantum physics in simple terms', 'Top 5 healthy breakfast recipes', etc.)"
            rows={4}
            style={{ 
              width: "100%", 
              padding: 12,
              border: "1px solid #d1d5db",
              borderRadius: 6,
              fontSize: 16,
              resize: "vertical"
            }}
            required
          />
          <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>
            Be specific about what you want - the AI will generate a complete script from this description.
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label style={{ display: "block", fontWeight: "500", marginBottom: 8 }}>
              Duration (seconds)
            </label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              min={15}
              max={300}
              step={15}
              style={{ 
                width: "100%", 
                padding: 12,
                border: "1px solid #d1d5db",
                borderRadius: 6,
                fontSize: 16
              }}
              required
            />
          </div>

          <div>
            <label style={{ display: "block", fontWeight: "500", marginBottom: 8 }}>
              Voice Style
            </label>
            <select
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              style={{ 
                width: "100%", 
                padding: 12,
                border: "1px solid #d1d5db",
                borderRadius: 6,
                fontSize: 16
              }}
              required
            >
              <option value="nova">Nova (Friendly)</option>
              <option value="alloy">Alloy (Professional)</option>
              <option value="echo">Echo (Warm)</option>
              <option value="fable">Fable (Expressive)</option>
            </select>
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          style={{
            padding: "16px 24px",
            backgroundColor: loading ? "#9ca3af" : "#3b82f6",
            color: "white",
            border: "none",
            borderRadius: 8,
            fontSize: 16,
            fontWeight: "500",
            cursor: loading ? "not-allowed" : "pointer",
            marginTop: 8
          }}
        >
          {loading ? "Generating Video..." : "Generate Video"}
        </button>
      </form>

      {runId && (
        <div style={{ 
          marginTop: 24, 
          padding: 16, 
          backgroundColor: "#f0fdf4", 
          border: "1px solid #22c55e",
          borderRadius: 8,
          textAlign: "center"
        }}>
          <p style={{ margin: 0, color: "#15803d", fontWeight: "500" }}>
            Video generation started! 
          </p>
          <p style={{ margin: "4px 0 0 0", fontSize: 12, color: "#16a34a" }}>
            Run ID: {runId}
          </p>
        </div>
      )}
      
      {error && (
        <div style={{ 
          marginTop: 16, 
          padding: 16, 
          backgroundColor: "#fef2f2", 
          border: "1px solid #ef4444",
          borderRadius: 8,
          color: "#dc2626"
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}
