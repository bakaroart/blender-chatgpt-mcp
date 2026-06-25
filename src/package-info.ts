import { readFileSync } from "node:fs";
import { join } from "node:path";
import { z } from "zod";

const packageSchema = z.object({
  version: z.string()
});

export const getPackageVersion = (): string => {
  try {
    const packageJson = JSON.parse(readFileSync(join(process.cwd(), "package.json"), "utf8")) as unknown;
    return packageSchema.parse(packageJson).version;
  } catch {
    return "0.0.0";
  }
};
