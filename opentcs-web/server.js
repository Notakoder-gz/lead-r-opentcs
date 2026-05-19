const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

// Serve static frontend files
app.use(express.static(path.join(__dirname, 'public')));

// OpenTCS Web API base URL (Kernel port 55200)
// The kernel host will be passed via environment variable or default to localhost
const OPENTCS_URL = process.env.OPENTCS_URL || 'http://localhost:55200';

// Proxy API requests to OpenTCS Kernel
app.get('/api/vehicles', async (req, res) => {
    try {
        const response = await axios.get(`${OPENTCS_URL}/v1/vehicles`);
        res.json(response.data);
    } catch (error) {
        console.error('Error fetching vehicles:', error.message);
        res.status(500).json({ error: 'Failed to fetch vehicles from OpenTCS' });
    }
});

app.get('/api/transportOrders', async (req, res) => {
    try {
        const response = await axios.get(`${OPENTCS_URL}/v1/transportOrders`);
        res.json(response.data);
    } catch (error) {
        console.error('Error fetching orders:', error.message);
        res.status(500).json({ error: 'Failed to fetch transport orders' });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`OpenTCS Web Frontend running on port ${PORT}`);
    console.log(`Connecting to OpenTCS at ${OPENTCS_URL}`);
});
