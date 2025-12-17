-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "name" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Analysis" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "empresa" TEXT NOT NULL,
    "ano" INTEGER NOT NULL,
    "trimestre" TEXT NOT NULL,
    "nota_final" DOUBLE PRECISION NOT NULL,
    "receita_nota" DOUBLE PRECISION NOT NULL,
    "lucro_nota" DOUBLE PRECISION NOT NULL,
    "divida_nota" DOUBLE PRECISION NOT NULL,
    "rentabilidade_nota" DOUBLE PRECISION NOT NULL,
    "soma_total" DOUBLE PRECISION NOT NULL,
    "qtde_tri" INTEGER NOT NULL,
    "media" DOUBLE PRECISION NOT NULL,
    "tese_investimento" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Analysis_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- AddForeignKey
ALTER TABLE "Analysis" ADD CONSTRAINT "Analysis_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
