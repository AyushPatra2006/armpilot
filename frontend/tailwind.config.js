module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ap: {
          bg: "#12151a",
          surface: "#1b1f26",
          border: "#2a2f38",
          text: "#e8eaed",
          dim: "#8b929e",
          accent: "#5eead4",
          warn: "#f5a623",
        },
      },
      fontFamily: {
        display: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "SF Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
