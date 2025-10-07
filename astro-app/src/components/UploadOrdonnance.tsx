import React, { useEffect, useState } from "react";

type Me = { id: number; email?: string };

const API_BASE = import.meta.env.PUBLIC_API_BASE_URL || "http://localhost:8080";

async function getMe(): Promise<Me | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { credentials: "include" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default function UploadOrdonnance() {
  const [me, setMe] = useState<Me | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [validUntil, setValidUntil] = useState<string>("");
  const [ocrText, setOcrText] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getMe().then(setMe);
  }, []);

  async function envoyerOrdonnance() {
    setErr(null);
    setMsg(null);

    if (!me?.id) {
      setErr("Tu dois être connecté(e) pour scanner une ordonnance.");
      return;
    }

    if (!imageFile && !ocrText.trim()) {
      setErr("Ajoute une image OU colle du texte OCR.");
      return;
    }

    const fd = new FormData();
    fd.append("utilisateur_id", String(me.id));
    if (validUntil) fd.append("valid_until", validUntil);
    if (imageFile) fd.append("image", imageFile);
    if (!imageFile && ocrText.trim()) fd.append("ocr_text", ocrText.trim());

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/ordonnances/scan`, {
        method: "POST",
        body: fd,
        credentials: "include",
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j?.detail || `Erreur ${res.status}`);
      }
      const data = await res.json();
      setMsg("Ordonnance créée !");
      window.location.href = `/ordonnance/ordonnance?id=${data.id}`;
    } catch (e: any) {
      setErr(e?.message ?? "Échec de l’envoi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto">
      <div className="bg-white rounded-2xl shadow p-5 space-y-4">
        <h1 className="text-xl font-bold text-[#0C3D2F]">
          Scanner une ordonnance
        </h1>

        {!me && (
          <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-3">
            Connecte-toi pour continuer.
          </div>
        )}

        <div className="space-y-2">
          <label className="block text-sm text-[#0C3D2F] font-medium">
            Image de l’ordonnance (PNG/JPG)
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-[#0FA06A] file:text-white hover:file:opacity-90"
          />
          <p className="text-xs text-gray-500">
            ou colle ci-dessous du texte OCR si tu n’as pas d’image :
          </p>
          <textarea
            value={ocrText}
            onChange={(e) => setOcrText(e.target.value)}
            rows={5}
            className="w-full rounded-lg border border-gray-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0FA06A]"
            placeholder={`Exemple :
Paracétamol 1/jour
Ibuprofène 2/jour
Amoxicilline 3 x par jour`}
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm text-[#0C3D2F] font-medium">
            Valide jusqu’au (optionnel)
          </label>
          <input
            type="date"
            value={validUntil}
            onChange={(e) => setValidUntil(e.target.value)}
            className="w-full rounded-lg border border-gray-200 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0FA06A]"
          />
        </div>

        {err && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
            {err}
          </div>
        )}
        {msg && (
          <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-3">
            {msg}
          </div>
        )}

        <button
          onClick={envoyerOrdonnance}
          disabled={loading || !me}
          className="w-full py-3 rounded-xl bg-[#0FA06A] text-white font-semibold disabled:opacity-50"
        >
          {loading ? "Envoi en cours..." : "Créer l’ordonnance"}
        </button>
      </div>

      <p className="text-xs text-gray-500 text-center mt-3">
        Les médicaments et la fréquence seront extraits automatiquement.
      </p>
    </div>
  );
}
