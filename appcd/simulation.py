
class ServiceState:
    def __init__(self, attack_damage_scale=1.0, recovery_rate=0.3,
                 capacity_threshold=60.0):
        self.capacity = 100.0
        self.response_time_ms = 50.0
        self.successful_attacks = 0
        self.blocked_legitimate = 0
        self.total_legitimate = 0
        self.total_attacks = 0
        self.resource_cost = 0.0
        self.attack_damage_scale = attack_damage_scale
        self.recovery_rate = recovery_rate
        self.capacity_threshold = capacity_threshold

    def apply_flow(self, is_attack: bool, action: str):
        if is_attack:
            self.total_attacks += 1
            damage, cost = self._attack_effect(action)
            damage *= self.attack_damage_scale
            self.capacity = max(0.0, self.capacity - damage)
            self.response_time_ms += damage * 2
            self.resource_cost += cost
            if action == "no_action":
                self.successful_attacks += 1
        else:
            self.total_legitimate += 1
            disrupted, cost = self._legitimate_effect(action, self.capacity)
            self.resource_cost += cost
            if disrupted:
                self.blocked_legitimate += 1

        self.capacity = min(100.0, self.capacity + self.recovery_rate)
        self.response_time_ms = max(50.0, self.response_time_ms - 1.0)

    def _attack_effect(self, action: str):
        return {
            "no_action":       (5.0, 0.0),
            "rate_limit":      (2.5, 0.5),
            "service_replica": (1.0, 2.0),
            "port_hop":        (0.5, 1.5),
        }[action]

    def _legitimate_effect(self, action: str, current_capacity: float):
        action_disruption, cost = {
            "no_action":       (False, 0.0),
            "rate_limit":      (False, 0.2),
            "service_replica": (False, 1.0),
            "port_hop":        (True,  0.8),
        }[action]
        capacity_disruption = current_capacity < self.capacity_threshold
        return (action_disruption or capacity_disruption), cost