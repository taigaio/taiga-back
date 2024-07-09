import taiga.webhooks.serializers


class TestCustomAttributesValuesWebhookSerializerMixin:
    webhook_serializer_mixin = (
        taiga.webhooks.serializers.CustomAttributesValuesWebhookSerializerMixin
    )

    def test_get_custom_attributes_values(self):
        assert (
            self.webhook_serializer_mixin().get_custom_attributes_values(None) is None
        )
