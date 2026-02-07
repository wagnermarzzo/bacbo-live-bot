function sendResult(result) {
  fetch(`/round?result=${result}`, { method: "POST" })
    .then(res => res.json())
    .then(data => {
      document.getElementById("signal").innerText = "Sinal: " + data.signal;
      document.getElementById("confidence").innerText = "Confiança: " + data.confidence + "%";
      document.getElementById("greens").innerText = data.greens;
      document.getElementById("reds").innerText = data.reds;
    });
}
