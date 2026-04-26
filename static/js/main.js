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
        
        // Generate UPI QR Code
        const qrContainer = document.getElementById('upi_qr_code');
        const upiSection = document.getElementById('upi_payment_section');
        
        if (qrContainer && upiSection && fare > 0) {
            qrContainer.innerHTML = "";
            const upiString = `upi://pay?pa=ashwinsenthil14@okicici&pn=Ashwin%20S&am=${fare.toFixed(2)}&cu=INR`;
            new QRCode(qrContainer, {
                text: upiString,
                width: 150,
                height: 150,
                colorDark : "#000000",
                colorLight : "#ffffff",
                correctLevel : QRCode.CorrectLevel.H
            });
            upiSection.style.display = 'block';
        } else if (upiSection) {
            upiSection.style.display = 'none';
        }
    }
}

async function handlePaymentSubmit(event) {
    event.preventDefault();
    
    const amount = document.getElementById('live_fare_input').value;
    const fromStop = document.getElementById('from_stop').value;
    const toStop = document.getElementById('to_stop').value;
    const passengerName = document.getElementById('passenger_name').value;
    const passengerPhone = document.getElementById('passenger_phone').value;
    const transactionId = document.getElementById('transaction_id') ? document.getElementById('transaction_id').value.trim() : null;
    
    if (!amount || amount == '0') {
        alert("Please select valid stops");
        return;
    }
    
    if (document.getElementById('transaction_id') && !transactionId) {
        alert("Please scan the QR code to pay, and enter the Transaction ID before generating the ticket.");
        document.getElementById('transaction_id').focus();
        return;
    }

    const btn = document.getElementById('pay_btn');
    btn.disabled = true;
    btn.innerText = "Processing...";
    
    try {
        const verifyResp = await fetch('/payments/verify/', {
            method: 'POST',
            body: JSON.stringify({
                bus_id: selectedBusId,
                from_stop: fromStop,
                to_stop: toStop,
                passenger_name: passengerName,
                passenger_phone: passengerPhone,
                amount: amount,
                razorpay_payment_id: transactionId || "pay_mock_" + Math.floor(Math.random() * 100000)
            }),
            headers: { 'Content-Type': 'application/json' }
        });
        const verifyData = await verifyResp.json();
        
        if (verifyData.success) {
            window.location.href = `/tickets/${verifyData.ticket_id}/`;
        } else {
            alert("Payment verification failed!");
        }
    } catch (e) {
        console.error(e);
        alert("An error occurred while generating the ticket.");
    } finally {
        btn.disabled = false;
        btn.innerText = "Generate Ticket";
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
