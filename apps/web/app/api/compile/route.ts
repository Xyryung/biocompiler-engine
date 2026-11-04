export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const response = await fetch(
      `${process.env.BIOCOMPILER_API_URL || "http://127.0.0.1:8000"}/compile`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(240_000),
        cache: "no-store",
      },
    );
    return Response.json(await response.json(), { status: response.status });
  } catch {
    return Response.json(
      {
        error: {
          code: "backend_unavailable",
          message:
            "The backend could not be reached. Start FastAPI and try again.",
        },
      },
      { status: 502 },
    );
  }
}
