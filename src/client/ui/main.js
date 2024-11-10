// Initalization
function on_init() {
    setup_switch(
        element_id("mode-switch"),
        function() {
            // TODO last | implement PROXY mode
        },
        function() {
            setTimeout(toggle_switch.bind(this,element_id("mode-switch"),false),150)
            // TODO 2nd | notificate about non-implemented PROXY mode
        }
    )
    
    // TODO 1st | connect to websocket and then:
    // - Get local device name
    // - Get active client list
    // - Send files
    // - Send selected mode
}

// Document
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

// Utility
let _elements = {}
function element_id(requested_id,force_reload) {
    if (force_reload || (!_elements[requested_id])) {
        _elements[requested_id] = document.getElementById(requested_id)
    }
    return _elements[requested_id]
}