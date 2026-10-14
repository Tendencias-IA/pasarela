// @ts-check
import js from "@eslint/js";
import jsxA11y from "eslint-plugin-jsx-a11y";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "dist",
      "coverage",
      "playwright-report",
      "test-results",
      "src/shared/api/types.gen.ts",
    ],
  },
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    extends: [...tseslint.configs.strictTypeChecked, jsxA11y.flatConfigs.recommended],
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
      globals: { ...globals.browser, ...globals.node },
    },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/ban-ts-comment": "error",
    },
  },
  {
    files: ["**/*.js"],
    languageOptions: { globals: { ...globals.node } },
  },
);
