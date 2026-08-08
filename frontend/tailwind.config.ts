import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0B0E14",
        panel: "#12161F",
        border: "#232838",
        accent: "#7C5CFF",
        accent2: "#33D6A6",
        danger: "#FF5C6C",
        muted: "#8A93A6",
      },
    },
  },
  plugins: [],
};
export default config;
