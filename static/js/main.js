let cachedStops = [];
let cachedFares = {};
let selectedBusId = null;

// Passenger flow: Load bus stops andfares
async function initPassengerFlow(busId) {
    selectedBusId = busId;
    try {
        const resp = await fetch(`/passenger/api/stops/${busId}/`);
        const data = await resp.json();
        cachedStops = data.stops;
        cachedFares = data.fares;
        populateFromStops();
    } catch (err) {
        console.error("Failed to load stops", err);
    }
}

function getStopName(stop) {
    return currentLang === 'ta' && stop.name_tamil ? stop.name_tamil : stop.name;
}

function populateFromStops() {
    const fromSelect = document.getElementById('from_stop');
    if (!fromSelect) return;
    
    fromSelect.innerHTML = `<option value="">-- Select Stop --</option>`;
    // Exclude the very last stop from 'From'
    for (let i = 0; i < cachedStops.length - 1; i++) {
        const stop = cachedStops[i];
        fromSelect.add(new Option(getStopName(stop), stop.id));
    }
}

// Ensure TO stop is strictly after FROM stop based on order
function onFromStopChange() {
    const fromId = document.getElementById('from_stop').value;
    const toSelect = document.getElementById('to_stop');
    
    toSelect.innerHTML = `<option value="">-- Select Stop --</option>`;
    document.getElementById('live_fare_display').innerText = `₹ 0.00`;
    document.getElementById('live_fare_input').value = '0';
    
    if (!fromId) return;
    
    const fromStopNode = cachedStops.find(s => s.id == fromId);
    
    for (let i = 0; i < cachedStops.length; i++) {
        const stop = cachedStops[i];
        if (stop.order > fromStopNode.order) {
            toSelect.add(new Option(getStopName(stop), stop.id));
        }
    }
}

function onToStopChange() {
    const fromId = document.getElementById('from_stop').value;
    const toId = document.getElementById('to_stop').value;
    
    if (fromId && toId) {
        const key = `${fromId}-${toId}`;
        const fare = cachedFares[key] || 0;
        document.getElementById('live_fare_display').innerText = `₹ ${fare.toFixed(2)}`;
        document.getElementById('live_fare_input').value = fare;
    }
}

async function handlePaymentSubmit(event) {
    event.preventDefault();
    const btn = document.getElementById('pay_btn');
    btn.disabled = true;
    btn.innerText = "Processing...";
    
    const amount = document.getElementById('live_fare_input').value;
    const fromStop = document.getElementById('from_stop').value;
    const toStop = document.getElementById('to_stop').value;
    const passengerName = document.getElementById('passenger_name').value;
    const passengerPhone = document.getElementById('passenger_phone').value;
    
    if (!amount || amount == '0') {
        alert("Please select valid stops");
        btn.disabled = false;
        btn.innerText = translations[currentLang]['pay_now'];
        return;
    }
    
    try {
        // Dummy create order API
        const orderResp = await fetch('/payments/create-order/', {
            method: 'POST',
            body: JSON.stringify({ amount: amount }),
            headers: { 'Content-Type': 'application/json' }
        });
        const orderData = await orderResp.json();
        
        // Simulating immediate success by sending right back to verify payment
        const verifyResp = await fetch('/payments/verify/', {
            method: 'POST',
            body: JSON.stringify({
                bus_id: selectedBusId,
                from_stop: fromStop,
                to_stop: toStop,
                passenger_name: passengerName,
                passenger_phone: passengerPhone,
                amount: amount,
                razorpay_order_id: orderData.order_id,
                razorpay_payment_id: "pay_mock_" + Math.floor(Math.random() * 100000)
            }),
            headers: { 'Content-Type': 'application/json' }
        });
        const verifyData = await verifyResp.json();
        
        if (verifyData.success) {
            window.location.href = `/tickets/${verifyData.ticket_id}/`;
        } else {
            alert("Payment failed!");
        }
    } catch (e) {
        console.error(e);
        alert("An error occurred during payment.");
    } finally {
        btn.disabled = false;
        btn.innerText = translations[currentLang]['pay_now'];
    }
}

window.addEventListener('languageChanged', () => {
    // Re-render dropdowns if on passenger home
    if (document.getElementById('from_stop')) {
        const oldFromId = document.getElementById('from_stop').value;
        const oldToId = document.getElementById('to_stop').value;
        
        populateFromStops();
        if (oldFromId) {
            document.getElementById('from_stop').value = oldFromId;
            onFromStopChange();
            if (oldToId) {
                document.getElementById('to_stop').value = oldToId;
            }
        }
    }
});
