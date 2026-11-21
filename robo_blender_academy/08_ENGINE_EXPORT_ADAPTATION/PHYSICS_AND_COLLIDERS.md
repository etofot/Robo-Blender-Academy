# 08. Физические Коллайдеры и Навигационные Сетки

| Суффикс | Движок Godot 4 | Unity / Unreal Engine |
| :--- | :--- | :--- |
| `-col` | Создает твердую коллизию `CollisionShape3D` с видимой сеткой | MeshCollider |
| `-colonly` | Создает коллизию и **удаляет** визуальный меш (невидимая стена) | Invisible Collision Volume |
| `-navmesh` | Превращает полигоны меша в проходимую зону для AI Navigation | NavMesh Surface |
| `-convcol` | Генерирует выпуклую оболочку (Convex Hull) для физических обломков | Convex Mesh Collider |
