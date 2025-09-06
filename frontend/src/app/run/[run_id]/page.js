"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

const STEPS = [
  "script_generation",
  "speech_generation", 
  "video_generation",
  "final_assembly",
];

export default function RunPage() {
  const params = useParams();
  const runId = useMemo(() => params?.run_id?.toString?.() ?? "", [params]);
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!runId) return;

    let cancelled = false;
    const fetchRun = async () => {
      try {
        const res = await fetch(`http://localhost:3000/jobs/${runId}/status`);
        if (!res.ok) {
          const txt = await res.text();
          throw new Error(txt || `Failed: ${res.status}`);
        }
        const data = await res.json();
        if (!cancelled) setRun(data);
      } catch (e) {
        if (!cancelled) setError(e.message || "Fetch error");
      }
    };

    // Initial fetch, then poll
    fetchRun();
    const id = setInterval(fetchRun, 2000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [runId]);

  const renderStep = (name) => {
    let status = "PENDING";
    
    if (run?.status === "completed") {
      status = "COMPLETED";
    } else if (run?.status === "processing" || run?.status === "in_progress") {
      // Determine which step is active based on progress
      const progress = run?.progress || 0;
      if (progress >= 20 && name === "script_generation") status = "COMPLETED";
      else if (progress >= 40 && name === "speech_generation") status = "COMPLETED";
      else if (progress >= 70 && name === "video_generation") status = "COMPLETED";
      else if (progress === 100) status = "COMPLETED";
      else if ((progress >= 20 && progress < 40 && name === "speech_generation") ||
               (progress >= 40 && progress < 70 && name === "video_generation") ||
               (progress >= 70 && progress < 100 && name === "final_assembly")) {
        status = "IN_PROGRESS";
      }
    } else if (run?.status === "failed") {
      status = "FAILED";
    }
    
    const color =
      status === "COMPLETED" ? "#10b981" : 
      status === "IN_PROGRESS" ? "#f59e0b" : 
      status === "FAILED" ? "#ef4444" :
      "#6b7280";
    
    // Display friendly names
    const displayNames = {
      "script_generation": "Generate Script",
      "speech_generation": "Generate Speech", 
      "video_generation": "Generate Video",
      "final_assembly": "Final Assembly"
    };
    
    return (
      <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          style={{
            display: "inline-block",
            minWidth: 100,
            padding: "4px 12px",
            borderRadius: 999,
            background: color,
            color: "white",
            fontSize: 12,
            fontWeight: "500",
          }}
        >
          {status}
        </span>
        <span>{displayNames[name] || name}</span>
      </div>
    );
  };

  return (
    <div style={{ maxWidth: 640, margin: "2rem auto", padding: 16 }}>
      <h1>Run: {runId}</h1>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      <div style={{ marginTop: 16, display: "grid", gap: 8 }}>
        {STEPS.map((s) => renderStep(s))}
      </div>

      <div style={{ marginTop: 24 }}>
        <strong>Status:</strong> {run?.status || "PENDING"}
      </div>
      
      {run?.progress !== undefined && (
        <div style={{ marginTop: 16 }}>
          <strong>Progress:</strong> {run.progress}%
          <div style={{ 
            width: "100%", 
            height: 8, 
            backgroundColor: "#e5e7eb", 
            borderRadius: 4, 
            marginTop: 4 
          }}>
            <div style={{ 
              width: `${run.progress}%`, 
              height: "100%", 
              backgroundColor: "#3b82f6", 
              borderRadius: 4,
              transition: "width 0.3s ease"
            }} />
          </div>
        </div>
      )}
      
      {run?.message && (
        <div style={{ marginTop: 16 }}>
          <strong>Message:</strong> {run.message}
        </div>
      )}

      {run?.status === "completed" && run?.result?.video_file && (
        <div style={{ marginTop: 24 }}>
          <h3>Generated Video:</h3>
          <div style={{ marginTop: 16 }}>
            <video 
              controls 
              style={{ 
                width: "100%", 
                maxWidth: 600, 
                borderRadius: 8,
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
              }}
              src={`http://localhost:3000/jobs/${runId}/download`}
            >
              Your browser does not support the video tag.
            </video>
            <div style={{ marginTop: 12, textAlign: "center" }}>
              <a 
                href={`http://localhost:3000/jobs/${runId}/download`}
                download={`generated_video_${runId}.mp4`}
                style={{
                  display: "inline-block",
                  padding: "12px 24px", 
                  backgroundColor: "#10b981", 
                  color: "white", 
                  textDecoration: "none",
                  borderRadius: 8,
                  fontSize: 16,
                  fontWeight: "500"
                }}
              >
                Download Video
              </a>
            </div>
          </div>
        </div>
      )}
      
      {run?.error && (
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          backgroundColor: "#fef2f2", 
          border: "1px solid #ef4444", 
          borderRadius: 8,
          color: "#dc2626"
        }}>
          <strong>Error:</strong> {run.error}
        </div>
      )}
      
      {run?.result && (
        <div style={{ marginTop: 16 }}>
          <strong>Processing Time:</strong> {Math.round(run.result.processing_time || 0)} seconds
        </div>
      )}
    </div>
  );
}

