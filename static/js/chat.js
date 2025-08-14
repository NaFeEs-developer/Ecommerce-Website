(function(){
	const messagesEl = document.getElementById('chat-messages');
	const inputEl = document.getElementById('chat-text');
	const sendBtn = document.getElementById('chat-send');
	if(!messagesEl || !inputEl || !sendBtn) return;

	function addMessage(text, who){
		const div = document.createElement('div');
		div.className = 'msg ' + (who || 'bot');
		div.textContent = text;
		messagesEl.appendChild(div);
		messagesEl.scrollTop = messagesEl.scrollHeight;
	}

	let ws = null;
	function connectWS(){
		try{
			const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
			ws = new WebSocket(`${scheme}://${location.host}/ws/chat/`);
			ws.onopen = () => addMessage('Connected. Ask me about products!', 'bot');
			ws.onmessage = (e) => {
				try{ const data = JSON.parse(e.data); addMessage(data.message || '', 'bot'); }catch{}
			};
			ws.onclose = () => { ws = null; };
		}catch(err){ ws = null; }
	}
	connectWS();

	async function send(){
		const text = inputEl.value.trim();
		if(!text) return;
		addMessage(text, 'user');
		inputEl.value = '';
		if(ws && ws.readyState === WebSocket.OPEN){
			ws.send(JSON.stringify({message: text}));
			return;
		}
		try{
			const form = new FormData();
			form.append('message', text);
			const csrf = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1];
			const res = await fetch('/api/chat/', { method: 'POST', headers: {'X-CSRFToken': csrf}, body: form });
			const data = await res.json();
			addMessage(data.reply || 'Sorry, I had trouble responding.');
		}catch(err){
			addMessage('Network error, please try again.');
		}
	}

	sendBtn.addEventListener('click', send);
	inputEl.addEventListener('keydown', function(e){ if(e.key==='Enter'){ send(); }});

	addMessage('Hi! I can help you explore products, categories, prices, and availability.');
})();
