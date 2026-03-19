class StatsService:
    def dashboard(self) -> dict:
        return {
            'today_order_count': 18,
            'today_gmv': 5280.0,
            'total_user_count': 1260,
            'pending_refund_count': 2,
        }


service = StatsService()
