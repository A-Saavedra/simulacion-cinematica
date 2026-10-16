# Simulación Cinemática de Intercepción Aérea Compuesta

Este repositorio contiene el código fuente, la deducción analítica formal, las diapositivas de defensa y los recursos de simulación del proyecto de **Física General (Semestre II-2026)** para la carrera de Ingeniería Informática de la **Universidad Mayor de San Simón (UMSS)**.

---

## Estructura del Repositorio

```
├── Simulacion_Cinematica.pdf # Informecompilado en LaTeX
├── presentacion-simulacion-cinematica.pptx # Diapositivas
├── simulation.py # Motor gráfico (Pygame / 60 FPS)
├── main.tex # Código fuente del informe técnico
├── portada.tex # Carátula
├── bibliografia.bib # Referencias bibliográficas
├── figuras/ # Capturas telemétricas, curvas y diagramas
└── logos/ # Escudos vectoriales institucionales

```

---

## Modelo Cinemático

El escenario modela una intercepción frontal aire-aire colineal a cota constante ($h = 3000\text{ m}$):
* **Caza Interceptor A (Eurofighter Typhoon):** MRU a $v_A = 250.00\text{ m/s}$ ($900\text{ km/h}$).
* **Blanco Hostil B:** MRU a $v_B = 100.00\text{ m/s}$ ($360\text{ km/h}$) en sentido opuesto.
* **Separación de detección ($t=0\text{ s}$):** $D_0 = 9750.00\text{ m}$.
* **Retardo de cómputo radar:** $t_s = 5.0\text{ s}$.
* **Fase propulsada activa (MRUA):** $t_p = 5.0\text{ s}$ con $a_m = 120.00\text{ m/s}^2$ hasta alcanzar $v_{\text{máx}} = 850.00\text{ m/s}$.
* **Fase inercial de crucero (MRU):** $t_c = 5.0\text{ s}$ hasta la colisión frontal.

### Resultados Clave ($Oxy$ en el Caza A)
* **Tiempo total de vuelo del misil ($t_{\text{vuelo}}$):** $10.00\text{ s}$
* **Tiempo acumulado del operativo ($t_{\text{total}}$):** $15.00\text{ s}$
* **Recorrido del proyectil ($\Delta x_{m,\text{total}}$):** $7000.00\text{ m}$
* **Punto de impacto global ($x_{\text{imp}}$):** $8250.00\text{ m}$

---

## Ejecución de la Simulación

### Requisitos
* Python 3.10+
* Pygame

```bash
pip install pygame
```

### Lanzar el entorno gráfico

```bash
python simulation.py
```

---

## Integrantes

1. **Baltazar Rivas Bryan** — *202602115@est.umss.edu*
2. **Marquez Chambi Angel Eduardo** — *201002453@est.umss.edu*
3. **Morales Vega Álvaro** — *202111104@est.umss.edu*
4. **Saavedra Veliz Alex Cristian** — *201901963@est.umss.edu*

* **Docente:** MSc. José Luis Mamani C.  
* **Materia:** Física General  
* **Institución:** Universidad Mayor de San Simón (FCyT)  

