# 04. Автоматическое Выравнивание Моделей через PCA / SVD

При импорте сторонних моделей техники они часто развернуты под произвольными углами.  
Алгоритм выравнивает технику строго по осям сцены:

1. **Главная ось (Major Axis) $\to$ Ось Y**: Нос и Хвост машины/самолета.
2. **Вторичная ось (Medium Axis) $\to$ Ось X**: Размах крыльев или ширина корпуса.
3. **Третья ось (Minor Axis) $\to$ Ось Z**: Высота машины, направленная строго вверх.

```python
import bpy
import numpy as np

def align_model_pca(obj):
    verts = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
    centroid = np.mean(verts, axis=0)
    shifted = verts - centroid
    
    # Сингулярное разложение ковариационной матрицы
    cov = np.cov(shifted, rowvar=False)
    evals, evecs = np.linalg.eigh(cov)
    
    # Сортировка главных осей
    order = np.argsort(evals)[::-1]
    major_axis = evecs[:, order[0]]  # Вдоль длины
    medium_axis = evecs[:, order[1]] # Вдоль ширины
    minor_axis = evecs[:, order[2]]  # Вдоль высоты
    
    # Применение поворота в Blender
    # ...
```
