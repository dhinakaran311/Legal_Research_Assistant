const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  await prisma.user.create({
    data: {
      name: "Admin User",
      email: "admin@example.com",
      password: "hashedpassword123", // replace later with bcrypt
      role: "ADMIN",
    },
  });

  await prisma.document.create({
    data: {
      title: "Criminal Procedure Code, Section 438",
      content: "Anticipatory bail provision details...",
      source: "IndiaCode",
    },
  });
}

main()
  .then(() => console.log("✅ Seed data added"))
  .catch(console.error)
  .finally(() => prisma.$disconnect());