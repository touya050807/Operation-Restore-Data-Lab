/* ============================================================================
   index.js — logika Landing Page
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
  initParticles();

  const story = `> INCOMING TRANSMISSION — DATA LAB ITSB\n\n` +
    `Sebuah serangan siber besar-besaran melumpuhkan seluruh server kampus.\n` +
    `Python Runtime, Problem Analysis Center, Database Validation, Algorithm\n` +
    `Engine, dan Knowledge Core — SEMUA OFFLINE.\n\n` +
    `Kelompok kalian ditugaskan sebagai EMERGENCY DATA RECOVERY TEAM.\n` +
    `Selesaikan kelima mission untuk mengumpulkan Mission Code, lalu bawa ke\n` +
    `meja panitia Final Mission untuk mendapatkan Final Code dan membuka akses\n` +
    `Main Server sepenuhnya.\n\n` +
    `> PILIH KELOMPOK UNTUK MEMULAI.`;

  const storyEl = document.getElementById("storyText");
  let i = 0;
  function typeChar() {
    if (i <= story.length) {
      storyEl.textContent = story.slice(0, i);
      i++;
      setTimeout(typeChar, 13);
    }
  }
  typeChar();
});
