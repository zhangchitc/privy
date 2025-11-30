const API_BASE = '/api';

// Helper function to show result
function showResult(elementId, data, isError = false, isLoading = false) {
    const element = document.getElementById(elementId);
    element.className = 'result';
    
    if (isLoading) {
        element.className += ' loading';
        element.innerHTML = '<span class="spinner"></span>Processing...';
        element.style.display = 'block';
        return;
    }
    
    if (isError) {
        element.className += ' error';
        element.innerHTML = `<pre>Error: ${data}</pre>`;
    } else {
        element.className += ' success';
        element.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
}

// Helper function to make API calls
async function apiCall(endpoint, data, resultElementId) {
    try {
        showResult(resultElementId, '', false, true);
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        const result = await response.json();
        
        if (result.success) {
            showResult(resultElementId, result.data, false);
            return result.data;
        } else {
            showResult(resultElementId, result.error || 'Unknown error', true);
            return null;
        }
    } catch (error) {
        showResult(resultElementId, error.message, true);
        return null;
    }
}

// Step 1: Create Wallet
document.getElementById('createWalletBtn').addEventListener('click', async () => {
    const result = await apiCall('/create-wallet', {}, 'walletResult');
    if (result && result.id) {
        // Auto-fill wallet ID in subsequent steps
        document.getElementById('walletId').value = result.id;
        document.getElementById('addKeyWalletId').value = result.id;
        document.getElementById('depositWalletId').value = result.id;
        document.getElementById('holdingWalletId').value = result.id;
        document.getElementById('orderWalletId').value = result.id;
        document.getElementById('getOrdersWalletId').value = result.id;
        document.getElementById('cancelWalletId').value = result.id;
        document.getElementById('withdrawWalletId').value = result.id;
    }
});

// Step 2: Register Orderly Account
document.getElementById('registerOrderlyBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('walletId').value;
    const chainId = document.getElementById('registerChainId').value;
    
    if (!walletId) {
        showResult('registerResult', 'Wallet ID is required', true);
        return;
    }
    
    await apiCall('/register-orderly', {
        walletId,
        chainId: chainId ? parseInt(chainId) : undefined,
    }, 'registerResult');
});

// Step 3: Add Orderly Key
document.getElementById('addKeyBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('addKeyWalletId').value;
    const chainId = document.getElementById('addKeyChainId').value;
    
    if (!walletId) {
        showResult('addKeyResult', 'Wallet ID is required', true);
        return;
    }
    
    await apiCall('/add-orderly-key', {
        walletId,
        chainId: chainId ? parseInt(chainId) : undefined,
    }, 'addKeyResult');
});

// Step 4: Deposit USDC
document.getElementById('depositBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('depositWalletId').value;
    const amount = document.getElementById('depositAmount').value;
    const chainId = document.getElementById('depositChainId').value;
    
    if (!walletId || !amount) {
        showResult('depositResult', 'Wallet ID and Amount are required', true);
        return;
    }
    
    await apiCall('/deposit-usdc', {
        walletId,
        amount,
        chainId: chainId ? parseInt(chainId) : undefined,
    }, 'depositResult');
});

// Step 5: Get Holdings
document.getElementById('getHoldingBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('holdingWalletId').value;
    
    if (!walletId) {
        showResult('holdingResult', 'Wallet ID is required', true);
        return;
    }
    
    await apiCall('/get-holding', {
        walletId,
        all: false,
    }, 'holdingResult');
});

// Step 6: Create Order
document.getElementById('createOrderBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('orderWalletId').value;
    const symbol = document.getElementById('orderSymbol').value;
    const orderType = document.getElementById('orderType').value;
    const side = document.getElementById('orderSide').value;
    const orderPrice = document.getElementById('orderPrice').value;
    const orderQuantity = document.getElementById('orderQuantity').value;
    
    if (!walletId || !symbol || !orderType || !side) {
        showResult('createOrderResult', 'Wallet ID, Symbol, Order Type, and Side are required', true);
        return;
    }
    
    const orderData = {
        walletId,
        symbol,
        orderType,
        side,
    };
    
    if (orderPrice) {
        orderData.orderPrice = parseFloat(orderPrice);
    }
    
    if (orderQuantity) {
        orderData.orderQuantity = parseFloat(orderQuantity);
    }
    
    const result = await apiCall('/create-order', orderData, 'createOrderResult');
    if (result && result.orderId) {
        // Auto-fill order ID in cancel order form
        document.getElementById('cancelOrderId').value = result.orderId;
        document.getElementById('cancelSymbol').value = symbol;
    }
});

// Step 7: Get Orders
document.getElementById('getOrdersBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('getOrdersWalletId').value;
    const status = document.getElementById('orderStatus').value;
    
    if (!walletId) {
        showResult('getOrdersResult', 'Wallet ID is required', true);
        return;
    }
    
    const orderData = { walletId };
    if (status) {
        orderData.status = status;
    }
    
    await apiCall('/get-orders', orderData, 'getOrdersResult');
});

// Step 8: Cancel Order
document.getElementById('cancelOrderBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('cancelWalletId').value;
    const orderId = document.getElementById('cancelOrderId').value;
    const symbol = document.getElementById('cancelSymbol').value;
    
    if (!walletId || !orderId || !symbol) {
        showResult('cancelOrderResult', 'Wallet ID, Order ID, and Symbol are required', true);
        return;
    }
    
    await apiCall('/cancel-order', {
        walletId,
        orderId: parseInt(orderId),
        symbol,
    }, 'cancelOrderResult');
});

// Step 9: Withdraw USDC
document.getElementById('withdrawBtn').addEventListener('click', async () => {
    const walletId = document.getElementById('withdrawWalletId').value;
    const amount = document.getElementById('withdrawAmount').value;
    const token = document.getElementById('withdrawToken').value || 'USDC';
    const chainId = document.getElementById('withdrawChainId').value;
    
    if (!walletId || !amount) {
        showResult('withdrawResult', 'Wallet ID and Amount are required', true);
        return;
    }
    
    await apiCall('/withdraw-usdc', {
        walletId,
        amount,
        token,
        chainId: chainId ? parseInt(chainId) : undefined,
    }, 'withdrawResult');
});

