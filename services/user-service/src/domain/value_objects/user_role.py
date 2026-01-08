"""
UserRole - Value Object representing user roles in the system.

В системе есть 4 типа пользователей:
- Customer: обычный пользователь, заказывает еду
- Courier: курьер, доставляет заказы
- RestaurantOwner: владелец ресторана, управляет меню
- Admin: администратор системы
"""

from enum import Enum


class UserRole(str, Enum):
    """
    Роли пользователей в системе.

    Наследуемся от str для:
    1. Автоматической сериализации в JSON (FastAPI)
    2. Совместимости с PostgreSQL enum типом
    3. Читаемости в логах и базе данных

    Примеры:
        >>> role = UserRole.CUSTOMER
        >>> str(role)
        'customer'
        >>> role.value
        'customer'
        >>> UserRole('customer')
        <UserRole.CUSTOMER: 'customer'>
    """

    CUSTOMER = "customer"
    COURIER = "courier"
    RESTAURANT_OWNER = "restaurant_owner"
    ADMIN = "admin"

    def __str__(self) -> str:
        """String representation for logging and display."""
        return self.value

    @property
    def display_name(self) -> str:
        """
        Human-readable name for UI.

        Returns:
            str: Formatted role name
        """
        names = {
            self.CUSTOMER: "Customer",
            self.COURIER: "Courier",
            self.RESTAURANT_OWNER: "Restaurant Owner",
            self.ADMIN: "Administrator",
        }
        return names[self]

    @property
    def permissions(self) -> set[str]:
        """
        Базовые права доступа для роли.

        В будущем можно расширить для RBAC (Role-Based Access Control).

        Returns:
            set[str]: Набор разрешений для роли
        """
        permissions_map = {
            self.CUSTOMER: {"create_order", "view_own_orders", "update_profile"},
            self.COURIER: {
                "view_assigned_deliveries",
                "update_delivery_status",
                "update_location",
                "update_profile",
            },
            self.RESTAURANT_OWNER: {
                "manage_restaurant",
                "manage_menu",
                "view_orders",
                "update_profile",
            },
            self.ADMIN: {
                "manage_users",
                "manage_restaurants",
                "view_all_orders",
                "view_analytics",
            },
        }
        return permissions_map[self]
