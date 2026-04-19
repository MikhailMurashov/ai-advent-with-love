from channels.webhook import WebhookChannel

channel_registry: dict[str, "WebhookChannel"] = {
    "webhook": WebhookChannel(),
}
