import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

const DATA_DIR = path.resolve(process.cwd(), "../data/text");

export async function GET(
  _request: Request,
  { params }: { params: { paperId: string } }
) {
  try {
    const filePath = path.join(DATA_DIR, `${params.paperId.replace(".json", "")}_cleaned.json`);
    const content = await fs.readFile(filePath, "utf-8");
    return NextResponse.json(JSON.parse(content));
  } catch {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
}
