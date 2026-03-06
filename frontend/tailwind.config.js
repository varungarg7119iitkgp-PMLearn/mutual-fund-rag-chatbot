/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          main: "#0B0E11",
          elevated: "#11151A",
          subtle: "#1B1F23",
          panel: "#11151B",
          ticker: "#05070A",
        },
        border: {
          subtle: "#22262B",
          strong: "#32363C",
        },
        accent: {
          growth: "#00C805",
          attention: "#FFC857",
          neutral: "#7B8BA1",
        },
        danger: "#FF3B4A",
        success: "#19C57D",
        text: {
          primary: "#F5F7FA",
          secondary: "#A6B1C2",
          muted: "#6D7685",
          inverse: "#050608",
        },
      },
      fontFamily: {
        sans: ["Poppins", "system-ui", "ui-sans-serif", "sans-serif"],
      },
      boxShadow: {
        "glow-accent":
          "0 0 0 1px rgba(0,200,5,0.5), 0 0 24px rgba(0,200,5,0.12)",
        "card-elevated":
          "0 18px 45px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(16, 24, 40, 0.75)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: 0, transform: "translateY(8px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        "ticker-pulse": {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.7 },
        },
        "slide-in-left": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
        "slide-in-right": {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 220ms ease-out",
        "ticker-pulse": "ticker-pulse 2.8s ease-in-out infinite",
        "slide-in-left": "slide-in-left 250ms ease-out",
        "slide-in-right": "slide-in-right 250ms ease-out",
      },
    },
  },
  plugins: [],
};

