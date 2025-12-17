import { defineConfig, env } from "prisma/config";
import "dotenv/config";

export default defineConfig({
  // Aponta para onde está seu schema
  schema: "prisma/schema.prisma",
  datasource: {
    // A URL de conexão entra aqui agora
    url: env("DATABASE_URL"),
  },
});