import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
        tsconfigRootDir: import.meta.dirname
      }
    },
    ignores: ["dist/**", "node_modules/**", "coverage/**", "eslint.config.js"]
  },
  {
    files: ["**/*.ts"],
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": [
        "error",
        {
          "checksVoidReturn": false
        }
      ]
    }
  },
  {
    files: ["tests/**/*.ts"],
    rules: {
      "@typescript-eslint/no-non-null-assertion": "off"
    }
  }
);
