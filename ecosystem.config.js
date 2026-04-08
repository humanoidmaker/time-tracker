module.exports = {
  apps: [
    {
      name: "time-tracker-backend",
      cwd: "./backend",
      script: "uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "python3",
      env: {
        PORT: 8000,
        MONGODB_URI: "mongodb://localhost:27017/time_tracker",
        JWT_SECRET: "change-in-production",
      },
      max_restarts: 10,
      watch: false,
    },    {
      name: "time-tracker-frontend",
      cwd: "./frontend",
      script: "npx",
      args: "vite --host 0.0.0.0 --port 3000",
      env: {
        PORT: 3000,
      },
      max_restarts: 10,
      watch: false,
    }
  ],
};
