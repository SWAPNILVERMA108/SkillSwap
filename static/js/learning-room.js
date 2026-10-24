(() => {
  const cfg = window.SKILLSWAP_ROOM;
  const $ = (id) => document.getElementById(id);
  const localVideo = $("localVideo"), remoteVideo = $("remoteVideo"), state = $("callStatus");
  let ws = null, pc = null, localStream = null, screenStream = null, makingOffer = false;
  const initiator = Number(cfg.userId) < Number(cfg.peerId);
  const rtcConfig = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

  function connectSocket() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
    const scheme = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${scheme}//${location.host}${cfg.websocketPath}`);
    ws.onopen = () => { state.textContent = "Secure WebSocket signaling connected. Start camera and microphone to join."; };
    ws.onmessage = async (event) => {
      let msg; try { msg = JSON.parse(event.data); } catch { return; }
      try {
        if (msg.type === "participant_joined") {
          if (initiator && localStream) await createOffer();
          state.textContent = "Participant connected. Waiting for media negotiation.";
        } else if (msg.type === "offer") {
          await ensurePeer();
          await pc.setRemoteDescription(msg.data.description);
          await pc.setLocalDescription(await pc.createAnswer());
          send("answer", { description: pc.localDescription });
        } else if (msg.type === "answer" && pc && msg.data?.description) {
          if (pc.signalingState === "have-local-offer") await pc.setRemoteDescription(msg.data.description);
        } else if (msg.type === "ice_candidate" && pc && msg.data?.candidate) {
          try { await pc.addIceCandidate(msg.data.candidate); } catch (e) { console.warn("ICE candidate ignored", e); }
        } else if (msg.type === "participant_left") {
          state.textContent = "The other participant left the room.";
        } else if (msg.type === "error") state.textContent = msg.message || "Signaling error.";
      } catch (e) { console.error(e); state.textContent = `Call error: ${e.message}`; }
    };
    ws.onclose = () => { state.textContent = "Signaling disconnected. Refresh to reconnect."; };
    ws.onerror = () => { state.textContent = "WebSocket error. Check server and room permissions."; };
  }
  function waitForSocket() {
    if (ws?.readyState === WebSocket.OPEN) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("Signaling connection timed out. Refresh the page.")), 8000);
      const check = () => {
        if (ws?.readyState === WebSocket.OPEN) { clearTimeout(timeout); resolve(); }
        else if (!ws || ws.readyState === WebSocket.CLOSED) { clearTimeout(timeout); reject(new Error("Signaling connection is closed.")); }
        else setTimeout(check, 100);
      };
      check();
    });
  }
  function send(type, data = {}) {
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type, data }));
  }
  async function ensurePeer() {
    if (!pc) {
      pc = new RTCPeerConnection(rtcConfig);
      pc.onicecandidate = (e) => { if (e.candidate) send("ice_candidate", { candidate: e.candidate }); };
      pc.ontrack = (e) => { remoteVideo.srcObject = e.streams[0]; };
      pc.onconnectionstatechange = () => { state.textContent = `Call state: ${pc.connectionState}`; };
    }
    if (localStream) {
      localStream.getTracks().forEach(track => {
        const exists = pc.getSenders().some(sender => sender.track && sender.track.kind === track.kind);
        if (!exists) pc.addTrack(track, localStream);
      });
    }
    return pc;
  }
  async function startLocalMedia(negotiate = true) {
    if (!localStream) {
      localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
      localVideo.srcObject = localStream;
      $("shareScreen").disabled = false; $("stopMedia").disabled = false;
    }
    await ensurePeer();
    if (negotiate) await createOffer();
  }
  async function createOffer() {
    if (!pc || !localStream || makingOffer || pc.signalingState !== "stable") return;
    try { makingOffer = true; await pc.setLocalDescription(await pc.createOffer()); send("offer", { description: pc.localDescription }); }
    finally { makingOffer = false; }
  }
  $("startCall").addEventListener("click", async () => {
    try {
      if (!ws || ws.readyState === WebSocket.CLOSED) connectSocket();
      await waitForSocket();
      await startLocalMedia(true);
      $("startCall").disabled = true;
      state.textContent = initiator ? "Camera and microphone started. Waiting for peer or negotiating call." : "Camera and microphone started. Waiting for the other participant to initiate negotiation.";
    } catch (e) { state.textContent = `Could not start camera/microphone: ${e.message}`; }
  });
  $("shareScreen").addEventListener("click", async () => {
    try {
      if (!pc || !localStream) throw new Error("Start your camera/microphone first.");
      screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      const screenTrack = screenStream.getVideoTracks()[0];
      const videoSender = pc.getSenders().find(s => s.track?.kind === "video");
      if (videoSender) await videoSender.replaceTrack(screenTrack); else pc.addTrack(screenTrack, screenStream);
      screenTrack.onended = stopScreen;
      $("shareScreen").disabled = true; state.textContent = "Screen sharing is active.";
      send("screen_share_status", { active: true });
    } catch (e) { state.textContent = `Screen share failed: ${e.message}`; }
  });
  async function stopScreen() {
    if (screenStream) screenStream.getTracks().forEach(t => t.stop()); screenStream = null;
    const cameraTrack = localStream?.getVideoTracks()[0];
    const sender = pc?.getSenders().find(s => s.track?.kind === "video");
    if (sender && cameraTrack) await sender.replaceTrack(cameraTrack);
    $("shareScreen").disabled = !localStream; send("screen_share_status", { active: false });
  }
  $("stopMedia").addEventListener("click", () => {
    if (localStream) localStream.getTracks().forEach(t => t.stop());
    if (screenStream) screenStream.getTracks().forEach(t => t.stop());
    localStream = null; screenStream = null; localVideo.srcObject = null;
    $("shareScreen").disabled = true; $("stopMedia").disabled = true; $("startCall").disabled = false;
    state.textContent = "Local camera and microphone stopped. Refresh to restart the call cleanly.";
  });
  connectSocket();
  window.addEventListener("beforeunload", () => { if (ws) ws.close(); if (pc) pc.close(); if (localStream) localStream.getTracks().forEach(t => t.stop()); if (screenStream) screenStream.getTracks().forEach(t => t.stop()); });
})();
