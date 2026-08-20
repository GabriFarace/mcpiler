from fastapi import Body, FastAPI, HTTPException


app = FastAPI()


@app.get("/orders")
def list_orders() -> list[dict]:
    """List orders visible to the current user."""
    return order_store.list_orders()


@app.get("/orders/{order_id}")
def get_order(order_id: str) -> dict:
    """Return one order by identifier."""
    return order_store.get_order(order_id)


@app.post("/orders")
def create_order(order: dict = Body(...)) -> dict:
    """Create a new order."""
    return order_store.create_order(order)


@app.patch("/orders/{order_id}/address")
def update_order_address(order_id: str, address: dict = Body(...)) -> dict:
    """Update the delivery address before the order ships."""
    order = order_store.get_order(order_id)
    if order["status"] == "shipped":
        raise HTTPException(status_code=409, detail="A shipped order cannot change address")
    return order_store.update_address(order_id, address)


@app.post("/orders/{order_id}/refund")
def refund_order(order_id: str) -> dict:
    """Refund an eligible order through the payment provider."""
    return payment_gateway.refund_order(order_id)


@app.delete("/orders/{order_id}")
def delete_order(order_id: str) -> None:
    """Permanently delete an order."""
    order_store.delete_order(order_id)


@app.get("/internal/health")
def health() -> dict:
    """Report internal service health."""
    return {"status": "ok"}
