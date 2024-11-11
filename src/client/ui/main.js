let local_socket = null
let active_clients = []

// Initalization
function on_init() {
    setup_switch(
        element_id("mode-switch"),
        function() {
            // TODO last | implement PROXY mode
        },
        function() {
            setTimeout(toggle_switch.bind(this,element_id("mode-switch"),false),150)
            // TODO 2nd | notify about non-implemented PROXY mode
        }
    )
    connect_websocket(function() {
        refresh_clients()
        local_socket.addEventListener("message",function(event) {
            event.data.text().then(function(data_text) {
                let message_json = JSON.parse(data_text)
                if (message_json.type == "update_active") {
                    refresh_clients()
                }
            })
        })
    })
    
    // TODO 1st | connect to websocket and then:
    // - Get local device name
    // - Get active client list
    // - Send files
    // - Send selected mode
}

// Backend
function connect_websocket(open_callback) {
    if (local_socket && ((local_socket.readyState == WebSocket.OPEN) || (local_socket.readyState == WebSocket.CONNECTING))) {
        local_socket.close()
    }
    console.log("[INFO] Connecting socket...")
    local_socket = (new WebSocket("/websocket"))
    local_socket.addEventListener("open",open_callback)
    local_socket.addEventListener("error",function(event) {
        console.warn("[WARN] Lost socket, attempting to reconnect...")
        connect_websocket()
    })
}

function websocket_request(request_body) {
    request_body.id = random_string(32)
    let new_promise = (new Promise(function(resolve,reject) {
        let promise_listener = function(event) {
            event.data.text().then(function(data_text) {
                let response_json = JSON.parse(data_text)
                if (response_json.id !== request_body.id) {
                    return
                }
                local_socket.removeEventListener("message",promise_listener)
                resolve(response_json)
            })
        }
        local_socket.addEventListener("message",promise_listener)
    }))
    local_socket.send(JSON.stringify(request_body))
    return new_promise
}

// Document
function refresh_clients() {
    console.log("refreshing clients")
    websocket_request({
        "type": "active_clients"
    }).then(function(response_json) {
        let clients_before = Object.keys(active_clients)
        let clients_after = [response_json.self]
        if (!clients_before.includes(response_json.self)) {
            let new_self = _add_party(response_json.self,0.1,0.5)
            _set_party_info(new_self,"(You)")
            active_clients[response_json.self] = [new_self]
        }
        for (let new_client of response_json.active) {
            clients_after.push(new_client.name)
            if (!active_clients.includes(new_client)) {
                let new_party = _add_party(new_client.name,0.5,0.5)
                active_clients[new_client.name] = [new_party,new_client]
            }
        }
        let lost_clients = clients_before.filter(function(value) {
            return (!clients_after.includes(value))
        })
        for (let lost_client of lost_clients) {
            active_clients[lost_client][0].remove()
            delete active_clients[lost_client]
        }
    })
}

function setup_switch(switch_element,left_callback,right_callback) {
    let switch_frame = switch_element.getElementsByClassName("switch-frame")[0]
    let switch_left = switch_element.getElementsByClassName("switch-left")[0]
    let switch_right = switch_element.getElementsByClassName("switch-right")[0]

    switch_frame.classList.add("switch-left")
    
    switch_left.addEventListener("click",function() {
        if (!switch_frame.classList.contains("switch-right")) {
            return
        }
        switch_frame.classList.remove("switch-right")
        switch_frame.classList.add("switch-left")
        left_callback()
    })
    switch_right.addEventListener("click",function() {
        if (!switch_frame.classList.contains("switch-left")) {
            return
        }
        switch_frame.classList.remove("switch-left")
        switch_frame.classList.add("switch-right")
        right_callback()
    })
}

function toggle_switch(switch_element,state) {
    let switch_frame = switch_element.getElementsByClassName("switch-frame")[0]
    if (state === undefined) {
        state = switch_frame.classList.contains("switch-right")
    }
    if (state) {
        switch_frame.classList.remove("switch-left")
        switch_frame.classList.add("switch-right")
    } else {
        switch_frame.classList.remove("switch-right")
        switch_frame.classList.add("switch-left")
    }
}

function _add_party(name,x,y) {
    let new_container = document.createElement("div")
    new_container.setAttribute("class","party")
    new_container.style.left = `${String(x * 100)}%`
    new_container.style.top = `${String(y * 100)}%`
    let new_img = document.createElement("img")
    new_img.setAttribute("src","./assets/user.svg")
    new_container.appendChild(new_img)
    let new_span_name = document.createElement("span")
    new_span_name.setAttribute("class","party-name")
    new_span_name.innerText = name
    new_container.appendChild(new_span_name)
    let new_span_info = document.createElement("span")
    new_span_info.setAttribute("class","party-info")
    new_span_info.innerText = ""
    new_container.appendChild(new_span_info)
    document.body.appendChild(new_container)
    return new_container
}

function _set_party_info(party_element,info) {
    let party_span_info = party_element.getElementsByClassName("party-info")[0]
    party_span_info.innerText = info
}

// Utility
let _elements = {}
function element_id(requested_id,force_reload) {
    if (force_reload || (!_elements[requested_id])) {
        _elements[requested_id] = document.getElementById(requested_id)
    }
    return _elements[requested_id]
}

function random_string(length) {
    return Array.from({length},function() {
        return Math.random().toString(36)[2]
    }).join("")
}
