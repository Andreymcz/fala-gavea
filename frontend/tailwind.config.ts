import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        urgency: {
          alta: "#E53E3E",
          media: "#DD6B20",
          baixa: "#3182CE",
        },
        search: "#805AD5",
        success: "#38A169",
        error: "#E53E3E",
        neutral: "#718096",
        background: "#F7FAFC",
      },
    },
  },
  plugins: [],
} satisfies Config;
