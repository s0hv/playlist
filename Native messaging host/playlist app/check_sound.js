var port = null;

function sendNativeMessage() {
  var queryInfo = {
   audible: true
  };
 chrome.tabs.query(queryInfo, function(tabs){
  if (tabs.length > 0){
   port.postMessage("true");
  } else {
  port.postMessage("false");
  }
 });
}

function onNativeMessage(message) {
	console.log(message)
	console.log("recieved message ")
 sendNativeMessage();
}

function onDisconnected() {
 console.log("Disconnected")
 port = null;
}

function connect() {
 var hostName = "com.me.playlist";
 console.log(hostName)
 port = chrome.runtime.connectNative(hostName);
 port.onMessage.addListener(onNativeMessage);
 console.log(port)
 port.onDisconnect.addListener(onDisconnected);
}

connect();