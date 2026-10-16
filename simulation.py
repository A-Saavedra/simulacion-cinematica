import sys
import math
import random
import pygame

# --- 1. INICIALIZACIÓN Y CONFIGURACIÓN ---
pygame.init()
pygame.font.init()

ANCHO_VENTANA = 1480
ALTO_VENTANA = 940
pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
pygame.display.set_caption("Sistema de Intercepción Aérea Bietápico")
reloj = pygame.time.Clock()

# Paleta MFD Táctico Aeroespacial
FONDO_APP = (6, 9, 15)
FONDO_PANEL = (11, 16, 26)
FONDO_TARJETA = (16, 23, 36)
BORDE_PANEL = (25, 38, 58)
CYAN_HUD = (0, 229, 255)
VERDE_RADAR = (57, 255, 20)
ROJO_ALERTA = (255, 30, 86)
AMARILLO_TRAZO = (255, 200, 0)
NARANJA_PROP = (255, 140, 0)
AZUL_FUSELAJE = (0, 140, 220)
GRIS_GRID = (20, 32, 50)
GRIS_GRID_LIGHT = (35, 50, 75)
BLANCO_TEXTO = (240, 245, 255)
GRIS_TEXTO = (130, 145, 170)

# Fuentes
fuente_titulo = pygame.font.SysFont("Consolas", 13, bold=True)
fuente_subtitulo = pygame.font.SysFont("Consolas", 12, bold=True)
fuente_hud = pygame.font.SysFont("Consolas", 10)
fuente_hud_bold = pygame.font.SysFont("Consolas", 10, bold=True)
fuente_alerta = pygame.font.SysFont("Consolas", 16, bold=True)

# Variables de Entrada Configurables
str_D0 = "9750"
str_vA_kmh = "900"
str_vB_kmh = "360"
str_ts = "5.0"
str_tp = "5.0"
str_am = "120"

campo_activo = None
velocidad_sim = 1.0  # Factor (0.5x, 1x, 2x, 4x)
modo_grafico_fusionado = False  # Alterna vista de 3 gráficas vs 1 gráfica unificada

# Parámetros Físicos Calculados (Orientación Izquierda -> Derecha)
D_inicial = 9750.0
v_A_kmh = 900.0
v_B_kmh = 360.0
t_s = 5.0
t_p = 5.0
a_m = 120.0
h_cota = 3000.0
h_loft_real = 250.0
h_loft_2d = 35.0

v_A_ms = v_A_kmh / 3.6
v_B_ms = v_B_kmh / 3.6
v_max_misil = v_A_ms + a_m * t_p
d_s = D_inicial - (v_A_ms + v_B_ms) * t_s
d_prop = v_A_ms * t_p + 0.5 * a_m * (t_p ** 2)
gap_fin_prop = d_s - v_B_ms * t_p - d_prop
t_c = gap_fin_prop / (v_max_misil + v_B_ms) if (v_max_misil + v_B_ms) > 0 else 0
t_vuelo = t_p + t_c
t_total = t_s + t_vuelo
x_impacto = v_A_ms * t_s + d_prop + v_max_misil * t_c
dist_misil_total = d_prop + v_max_misil * t_c

wt_data = {
    "tvuelo": 10.19,
    "vmax": 890.0,
    "dist_misil": 7011.0,
    "ximp": 8236.0,
    "x_misil_wt": 6986.0
}

ANCHO_UTIL_2D = 680.0
ESCALA_X = ANCHO_UTIL_2D / D_inicial


def actualizar_parametros():
    global D_inicial, v_A_kmh, v_B_kmh, t_s, t_p, a_m, v_A_ms, v_B_ms
    global v_max_misil, d_s, d_prop, gap_fin_prop, t_c, t_vuelo, t_total
    global x_impacto, dist_misil_total, ESCALA_X

    try:
        D_inicial = max(1000.0, float(str_D0))
    except ValueError:
        D_inicial = 9750.0
    try:
        v_A_kmh = max(0.0, float(str_vA_kmh))
    except ValueError:
        v_A_kmh = 900.0
    try:
        v_B_kmh = max(0.0, float(str_vB_kmh))
    except ValueError:
        v_B_kmh = 360.0
    try:
        t_s = max(0.0, float(str_ts))
    except ValueError:
        t_s = 5.0
    try:
        t_p = max(0.1, float(str_tp))
    except ValueError:
        t_p = 5.0
    try:
        a_m = max(0.0, float(str_am))
    except ValueError:
        a_m = 120.0

    v_A_ms = v_A_kmh / 3.6
    v_B_ms = v_B_kmh / 3.6
    v_max_misil = v_A_ms + a_m * t_p
    d_s = D_inicial - (v_A_ms + v_B_ms) * t_s
    d_prop = v_A_ms * t_p + 0.5 * a_m * (t_p ** 2)
    gap_fin_prop = d_s - v_B_ms * t_p - d_prop

    if gap_fin_prop <= 0:
        b_rel = v_A_ms + v_B_ms
        tau = (-b_rel + math.sqrt(max(0, b_rel ** 2 + 2 * a_m * d_s))) / a_m if a_m > 0 else d_s / b_rel
        t_c = 0.0
        t_vuelo = tau
        dist_misil_total = v_A_ms * tau + 0.5 * a_m * (tau ** 2)
    else:
        v_rel = v_max_misil + v_B_ms
        t_c = gap_fin_prop / v_rel
        t_vuelo = t_p + t_c
        dist_misil_total = d_prop + v_max_misil * t_c

    t_total = t_s + t_vuelo
    x_impacto = v_A_ms * t_s + dist_misil_total
    ESCALA_X = ANCHO_UTIL_2D / D_inicial


def calcular_altitud_loft(x_m, max_elev=250.0):
    x_suelta = v_A_ms * t_s
    recorrido_total = x_impacto - x_suelta
    if x_m <= x_suelta or recorrido_total <= 0:
        return h_cota
    u = max(0.0, min(1.0, (x_m - x_suelta) / recorrido_total))
    return h_cota + 4.0 * max_elev * u * (1.0 - u)


# --- 2. CLASES Y ESTADO DE LA SIMULACIÓN ---
class ParticulaExplosion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        ang = random.uniform(0, 2 * math.pi)
        vel = random.uniform(40, 220)
        self.vx = math.cos(ang) * vel
        self.vy = math.sin(ang) * vel
        self.radio = random.uniform(3, 7)
        self.vida = 1.0
        self.color = random.choice([(255, 220, 0), (255, 120, 0), (255, 30, 86), (255, 255, 255)])

    def actualizar(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt * 1.3

    def dibujar(self, superficie):
        if self.vida > 0:
            r = max(1, int(self.radio * self.vida))
            pygame.draw.circle(superficie, self.color, (int(self.x), int(self.y)), r)


class EstadoSimulacion:
    def __init__(self):
        self.simulacion_iniciada = False
        self.en_pausa = False
        self.reiniciar()

    def reiniciar(self):
        actualizar_parametros()
        self.t = 0.0
        self.x_A = 0.0
        self.x_B = D_inicial
        self.x_m = 0.0
        self.y_m = h_cota
        self.v_m = v_A_ms
        self.fase_misil = "BODEGA"
        self.impacto_confirmado = False

        self.hist_x_A = []
        self.hist_x_B = []
        self.hist_x_m = []
        self.hist_y_m = []
        self.hist_v_m = []
        self.hist_D_rel = []
        self.particulas = []


sim = EstadoSimulacion()


# --- 3. DIBUJO DE INTERFAZ Y DIBUJOS TÁCTICOS ---
def dibujar_esquinas_hud(superficie, rect, color, tam=10, grosor=2):
    pygame.draw.line(superficie, color, (rect.x, rect.y), (rect.x + tam, rect.y), grosor)
    pygame.draw.line(superficie, color, (rect.x, rect.y), (rect.x, rect.y + tam), grosor)
    pygame.draw.line(superficie, color, (rect.right - tam, rect.y), (rect.right, rect.y), grosor)
    pygame.draw.line(superficie, color, (rect.right, rect.y), (rect.right, rect.y + tam), grosor)
    pygame.draw.line(superficie, color, (rect.x, rect.bottom - tam), (rect.x, rect.bottom), grosor)
    pygame.draw.line(superficie, color, (rect.x, rect.bottom), (rect.x + tam, rect.bottom), grosor)
    pygame.draw.line(superficie, color, (rect.right - tam, rect.bottom), (rect.right, rect.bottom), grosor)
    pygame.draw.line(superficie, color, (rect.right, rect.bottom - tam), (rect.right, rect.bottom), grosor)


def dibujar_contenedor(superficie, rect, titulo="", color_borde=CYAN_HUD):
    pygame.draw.rect(superficie, FONDO_PANEL, rect, border_radius=8)
    pygame.draw.rect(superficie, BORDE_PANEL, rect, 1, border_radius=8)
    dibujar_esquinas_hud(superficie, rect, color_borde, tam=12, grosor=2)
    if titulo:
        rect_tag = pygame.Rect(rect.x + 14, rect.y - 10, len(titulo) * 7 + 22, 20)
        pygame.draw.rect(superficie, FONDO_PANEL, rect_tag, border_radius=4)
        pygame.draw.rect(superficie, color_borde, rect_tag, 1, border_radius=4)
        txt = fuente_titulo.render(titulo, True, color_borde)
        superficie.blit(txt, (rect_tag.x + 8, rect_tag.y + 2))


def dibujar_tarjeta_mfd(superficie, rect, titulo):
    pygame.draw.rect(superficie, FONDO_TARJETA, rect, border_radius=6)
    pygame.draw.rect(superficie, BORDE_PANEL, rect, 1, border_radius=6)
    dibujar_esquinas_hud(superficie, rect, BORDE_PANEL, tam=6, grosor=1)
    txt = fuente_subtitulo.render(titulo, True, VERDE_RADAR)
    superficie.blit(txt, (rect.x + 10, rect.y + 5))


def dibujar_input_box_alineado(superficie, rect, texto, activo):
    col_bg = FONDO_PANEL if not activo else FONDO_TARJETA
    col_borde = AMARILLO_TRAZO if activo else CYAN_HUD
    pygame.draw.rect(superficie, col_bg, rect, border_radius=4)
    pygame.draw.rect(superficie, col_borde, rect, 1, border_radius=4)
    txt_surf = fuente_hud_bold.render(texto + ("|" if activo else ""), True, BLANCO_TEXTO)
    superficie.blit(txt_surf, (rect.x + 6, rect.y + 3))


def dibujar_leyenda(superficie, rect, items):
    y_off = rect.y + 6
    for color, texto in items:
        pygame.draw.rect(superficie, color, (rect.x + 6, y_off + 2, 8, 8), border_radius=2)
        lbl = fuente_hud.render(texto, True, BLANCO_TEXTO)
        superficie.blit(lbl, (rect.x + 20, y_off))
        y_off += 18


def dibujar_caza_eurofighter(superficie, x, y):
    pygame.draw.polygon(superficie, CYAN_HUD, [(x + 28, y), (x - 20, y - 7), (x - 18, y), (x - 20, y + 7)])
    pygame.draw.polygon(superficie, AZUL_FUSELAJE, [(x + 4, y), (x - 12, y - 22), (x - 3, y - 22)])
    pygame.draw.polygon(superficie, AZUL_FUSELAJE, [(x + 4, y), (x - 12, y + 22), (x - 3, y + 22)])
    pygame.draw.ellipse(superficie, BLANCO_TEXTO, (x + 6, y - 4, 12, 7))
    pygame.draw.line(superficie, CYAN_HUD, (x + 28, y), (x + 48, y), 1)


def dibujar_blanco_hostil(superficie, x, y):
    pygame.draw.polygon(superficie, ROJO_ALERTA, [(x - 24, y), (x + 18, y - 8), (x + 14, y), (x + 18, y + 8)])
    pygame.draw.polygon(superficie, (180, 20, 60), [(x - 2, y), (x + 10, y - 18), (x + 2, y - 18)])
    pygame.draw.polygon(superficie, (180, 20, 60), [(x - 2, y), (x + 10, y + 18), (x + 2, y + 18)])
    pygame.draw.line(superficie, ROJO_ALERTA, (x - 24, y), (x - 44, y), 1)


def dibujar_misil_aim120(superficie, x, y, color, ang_grados=0.0):
    surf = pygame.Surface((30, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, color, (2, 4, 20, 6))
    pygame.draw.polygon(surf, ROJO_ALERTA, [(22, 7), (18, 3), (18, 11)])
    surf_rot = pygame.transform.rotate(surf, -ang_grados)
    rect_rot = surf_rot.get_rect(center=(int(x), int(y)))
    superficie.blit(surf_rot, rect_rot.topleft)


# --- 4. RENDERIZADO DE GRÁFICAS ---
def renderizar_grafico_curva_x_vs_t(superficie, rect, t_max, x_max, pos_mouse=(0, 0)):
    pygame.draw.rect(superficie, FONDO_PANEL, rect, border_radius=6)
    pygame.draw.rect(superficie, BORDE_PANEL, rect, 1, border_radius=6)
    dibujar_esquinas_hud(superficie, rect, BORDE_PANEL, tam=8, grosor=1)

    lbl_tit = fuente_subtitulo.render("Curva Dinámica X vs T (Orientación +X)", True, CYAN_HUD)
    superficie.blit(lbl_tit, (rect.x + 12, rect.y + 8))

    mx, my, mb, mr = 50, 32, 25, 15
    g_rect = pygame.Rect(rect.x + mx, rect.y + my, rect.width - mx - mr, rect.height - my - mb)

    surf_alpha = pygame.Surface((g_rect.width, g_rect.height), pygame.SRCALPHA)
    px_ts = int((t_s / t_max) * g_rect.width)
    px_tp = int(((t_s + t_p) / t_max) * g_rect.width)
    px_tot = int((t_total / t_max) * g_rect.width)

    pygame.draw.rect(surf_alpha, (100, 110, 130, 20), (0, 0, px_ts, g_rect.height))
    pygame.draw.rect(surf_alpha, (255, 140, 0, 30), (px_ts, 0, max(0, px_tp - px_ts), g_rect.height))
    pygame.draw.rect(surf_alpha, (255, 30, 86, 20), (px_tp, 0, max(0, px_tot - px_tp), g_rect.height))
    superficie.blit(surf_alpha, (g_rect.x, g_rect.y))

    for i in range(5):
        t_val = (t_max / 4) * i
        px = g_rect.x + int((g_rect.width / 4) * i)
        pygame.draw.line(superficie, GRIS_GRID, (px, g_rect.y), (px, g_rect.bottom), 1)
        lbl_num = fuente_hud.render(f"{t_val:.0f}s", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (px - lbl_num.get_width() // 2, g_rect.bottom + 4))

        x_val = (x_max / 4) * i
        py = g_rect.bottom - int((g_rect.height / 4) * i)
        pygame.draw.line(superficie, GRIS_GRID, (g_rect.x, py), (g_rect.right, py), 1)
        lbl_num = fuente_hud.render(f"{x_val:.0f}", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (g_rect.x - lbl_num.get_width() - 4, py - 6))

    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.bottom), (g_rect.right, g_rect.bottom), 2)
    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.y), (g_rect.x, g_rect.bottom), 2)

    def val2px(t_val, x_val):
        nx = max(0.0, min(1.0, t_val / t_max))
        ny = max(0.0, min(1.0, x_val / x_max))
        return int(g_rect.x + nx * g_rect.width), int(g_rect.bottom - ny * g_rect.height)

    if len(sim.hist_x_A) >= 2:
        pts_A = [val2px(t, x) for t, x in sim.hist_x_A]
        pts_B = [val2px(t, x) for t, x in sim.hist_x_B]
        pygame.draw.aalines(superficie, CYAN_HUD, False, pts_A, 2)
        pygame.draw.aalines(superficie, VERDE_RADAR, False, pts_B, 2)

    if len(sim.hist_x_m) >= 2:
        pts_prop, pts_cruc = [], []
        for t_val, x_val, fase in sim.hist_x_m:
            px, py = val2px(t_val, x_val)
            if fase == "PROPULSION":
                pts_prop.append((px, py))
            elif fase == "CRUCERO":
                pts_cruc.append((px, py))

        if len(pts_prop) >= 2: pygame.draw.lines(superficie, NARANJA_PROP, False, pts_prop, 3)
        if len(pts_cruc) >= 2: pygame.draw.lines(superficie, ROJO_ALERTA, False, pts_cruc, 3)

        last_t, last_x, _ = sim.hist_x_m[-1]
        cpx, cpy = val2px(last_t, last_x)
        pygame.draw.circle(superficie, BLANCO_TEXTO, (cpx, cpy), 4)

    if sim.impacto_confirmado:
        ipx, ipy = val2px(t_total, x_impacto)
        pygame.draw.circle(superficie, ROJO_ALERTA, (ipx, ipy), 8)
        pygame.draw.circle(superficie, BLANCO_TEXTO, (ipx, ipy), 4)

    if g_rect.collidepoint(pos_mouse):
        mx_rel = pos_mouse[0] - g_rect.x
        t_hover = max(0.0, min(t_max, (mx_rel / g_rect.width) * t_max))
        pygame.draw.line(superficie, AMARILLO_TRAZO, (pos_mouse[0], g_rect.y), (pos_mouse[0], g_rect.bottom), 1)
        xA_h = v_A_ms * t_hover
        xB_h = D_inicial - v_B_ms * t_hover
        txt_h = fuente_hud_bold.render(f"t:{t_hover:.2f}s | xA:{xA_h:.0f}m | xB:{xB_h:.0f}m", True, AMARILLO_TRAZO)
        superficie.blit(txt_h, (min(g_rect.right - 220, pos_mouse[0] + 8), g_rect.y + 8))

    dibujar_leyenda(superficie, pygame.Rect(g_rect.x + 5, g_rect.y + 5, 130, 75), [
        (CYAN_HUD, "Caza A: xA(t)"),
        (VERDE_RADAR, "Blanco B: xB(t)"),
        (NARANJA_PROP, "Propulsado"),
        (ROJO_ALERTA, "Crucero")
    ])


def renderizar_grafico_loft_wt(superficie, rect, x_max, pos_mouse=(0, 0), y_min=1000.0, y_max=4000.0):
    pygame.draw.rect(superficie, FONDO_PANEL, rect, border_radius=6)
    pygame.draw.rect(superficie, BORDE_PANEL, rect, 1, border_radius=6)
    dibujar_esquinas_hud(superficie, rect, BORDE_PANEL, tam=8, grosor=1)

    lbl_tit = fuente_subtitulo.render("Trayectoria de vuelo (Perfil Loft War Thunder)", True, VERDE_RADAR)
    superficie.blit(lbl_tit, (rect.x + 12, rect.y + 8))

    mx, my, mb, mr = 50, 32, 25, 15
    g_rect = pygame.Rect(rect.x + mx, rect.y + my, rect.width - mx - mr, rect.height - my - mb)

    for i in range(5):
        x_val = (x_max / 4) * i
        px = g_rect.x + int((g_rect.width / 4) * i)
        pygame.draw.line(superficie, GRIS_GRID, (px, g_rect.y), (px, g_rect.bottom), 1)
        lbl_num = fuente_hud.render(f"{x_val:.0f}", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (px - lbl_num.get_width() // 2, g_rect.bottom + 4))

        y_val = y_min + ((y_max - y_min) / 4) * i
        py = g_rect.bottom - int((g_rect.height / 4) * i)
        pygame.draw.line(superficie, GRIS_GRID, (g_rect.x, py), (g_rect.right, py), 1)
        lbl_num = fuente_hud.render(f"{y_val:.0f}", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (g_rect.x - lbl_num.get_width() - 4, py - 6))

    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.bottom), (g_rect.right, g_rect.bottom), 2)
    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.y), (g_rect.x, g_rect.bottom), 2)

    def val2px(x_val, y_val):
        nx = max(0.0, min(1.0, x_val / x_max))
        ny = max(0.0, min(1.0, (y_val - y_min) / (y_max - y_min)))
        return int(g_rect.x + nx * g_rect.width), int(g_rect.bottom - ny * g_rect.height)

    py_cota = val2px(0, h_cota)[1]
    pygame.draw.line(superficie, GRIS_GRID_LIGHT, (g_rect.x, py_cota), (g_rect.right, py_cota), 1)

    x_suelta = v_A_ms * t_s
    px_suelta = val2px(x_suelta, h_cota)
    pygame.draw.circle(superficie, AMARILLO_TRAZO, px_suelta, 3)

    if len(sim.hist_x_m) >= 2:
        pts_loft = [val2px(x_m, y_m) for (t_val, x_m, _), y_m in zip(sim.hist_x_m, sim.hist_y_m)]
        pygame.draw.aalines(superficie, CYAN_HUD, False, pts_loft, 2)

        cpx, cpy = pts_loft[-1]
        pygame.draw.circle(superficie, BLANCO_TEXTO, (cpx, cpy), 4)

        curr_t = sim.hist_x_m[-1][0]
        curr_x_glob = sim.hist_x_m[-1][1]
        curr_y = sim.hist_y_m[-1]
        curr_v = sim.hist_v_m[-1][1]

        t_vuelo_actual = max(0.0, curr_t - t_s)
        dist_actual = max(0.0, curr_x_glob - x_suelta)

        tt_line1 = f"Tiempo de vuelo: {t_vuelo_actual:.2f} s"
        tt_line2 = f"Velocidad: {curr_v:.0f} m/s"
        tt_line3 = f"Distancia misil: {dist_actual:.0f} m"
        tt_line4 = f"Posición X(Global): {curr_x_glob:.0f} m, Y: {curr_y:.0f} m"

        s1 = fuente_hud.render(tt_line1, True, BLANCO_TEXTO)
        s2 = fuente_hud.render(tt_line2, True, BLANCO_TEXTO)
        s3 = fuente_hud.render(tt_line3, True, BLANCO_TEXTO)
        s4 = fuente_hud.render(tt_line4, True, CYAN_HUD)

        tt_w = max(s1.get_width(), s2.get_width(), s3.get_width(), s4.get_width()) + 14
        tt_h = 62

        box_x = min(g_rect.right - tt_w - 5,
                    max(g_rect.x + 5, cpx - tt_w - 10 if cpx + tt_w > g_rect.right else cpx + 10))
        box_y = max(g_rect.y + 5, min(g_rect.bottom - tt_h - 5, cpy - 20))

        rect_tt_box = pygame.Rect(box_x, box_y, tt_w, tt_h)
        pygame.draw.rect(superficie, FONDO_APP, rect_tt_box, border_radius=4)
        pygame.draw.rect(superficie, CYAN_HUD, rect_tt_box, 1, border_radius=4)

        superficie.blit(s1, (rect_tt_box.x + 7, rect_tt_box.y + 4))
        superficie.blit(s2, (rect_tt_box.x + 7, rect_tt_box.y + 18))
        superficie.blit(s3, (rect_tt_box.x + 7, rect_tt_box.y + 32))
        superficie.blit(s4, (rect_tt_box.x + 7, rect_tt_box.y + 46))

    if sim.impacto_confirmado:
        ipx, ipy = val2px(x_impacto, h_cota)
        pygame.draw.circle(superficie, ROJO_ALERTA, (ipx, ipy), 8)
        pygame.draw.circle(superficie, BLANCO_TEXTO, (ipx, ipy), 4)

    dibujar_leyenda(superficie, pygame.Rect(g_rect.x + 5, g_rect.y + 5, 140, 40), [
        (GRIS_GRID_LIGHT, "Cota 3000m"),
        (CYAN_HUD, "Trayectoria Loft")
    ])


def renderizar_grafico_velocidad_y_distancia(superficie, rect, t_max, v_max, D_max, pos_mouse=(0, 0)):
    pygame.draw.rect(superficie, FONDO_PANEL, rect, border_radius=6)
    pygame.draw.rect(superficie, BORDE_PANEL, rect, 1, border_radius=6)
    dibujar_esquinas_hud(superficie, rect, BORDE_PANEL, tam=8, grosor=1)

    lbl_tit = fuente_subtitulo.render("Perfil Vm(t) [Verde] & Distancia D_rel(t) [Cyan]", True, AMARILLO_TRAZO)
    superficie.blit(lbl_tit, (rect.x + 12, rect.y + 8))

    mx, my, mb, mr = 48, 34, 25, 15
    g_rect = pygame.Rect(rect.x + mx, rect.y + my, rect.width - mx - mr, rect.height - my - mb)

    for i in range(5):
        px = g_rect.x + int((g_rect.width / 4) * i)
        pygame.draw.line(superficie, GRIS_GRID, (px, g_rect.y), (px, g_rect.bottom), 1)
        lbl_num = fuente_hud.render(f"{(t_max / 4) * i:.0f}s", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (px - lbl_num.get_width() // 2, g_rect.bottom + 4))

        py = g_rect.bottom - int((g_rect.height / 4) * i)
        pygame.draw.line(superficie, GRIS_GRID, (g_rect.x, py), (g_rect.right, py), 1)
        lbl_num = fuente_hud.render(f"{(v_max / 4) * i:.0f}", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (g_rect.x - lbl_num.get_width() - 4, py - 6))

    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.bottom), (g_rect.right, g_rect.bottom), 2)
    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.y), (g_rect.x, g_rect.bottom), 2)

    if len(sim.hist_v_m) >= 2:
        pts_v = []
        for vt, vv in sim.hist_v_m:
            nx = max(0.0, min(1.0, vt / t_max))
            ny = max(0.0, min(1.0, vv / v_max))
            pts_v.append((int(g_rect.x + nx * g_rect.width), int(g_rect.bottom - ny * g_rect.height)))
        pygame.draw.lines(superficie, VERDE_RADAR, False, pts_v, 2)

    if len(sim.hist_D_rel) >= 2:
        pts_d = []
        for dt_val, dd in sim.hist_D_rel:
            nx = max(0.0, min(1.0, dt_val / t_max))
            ny = max(0.0, min(1.0, dd / D_max))
            pts_d.append((int(g_rect.x + nx * g_rect.width), int(g_rect.bottom - ny * g_rect.height)))
        pygame.draw.lines(superficie, CYAN_HUD, False, pts_d, 2)

    if len(sim.hist_v_m) >= 2:
        curr_v = sim.hist_v_m[-1][1]
        curr_d = sim.hist_D_rel[-1][1]
        lbl_tt = fuente_hud_bold.render(f"Vm:{curr_v:.0f}m/s | D:{curr_d:.0f}m", True, BLANCO_TEXTO)
        rect_tt = pygame.Rect(g_rect.x + 8, g_rect.y + 6, lbl_tt.get_width() + 10, 18)
        pygame.draw.rect(superficie, FONDO_APP, rect_tt, border_radius=3)
        pygame.draw.rect(superficie, VERDE_RADAR, rect_tt, 1, border_radius=3)
        superficie.blit(lbl_tt, (rect_tt.x + 5, rect_tt.y + 2))

    dibujar_leyenda(superficie, pygame.Rect(g_rect.right - 145, g_rect.y + 5, 140, 40), [
        (VERDE_RADAR, "Velocidad Vm(t)"),
        (CYAN_HUD, "Distancia D_rel(t)")
    ])


def renderizar_grafico_unificado(superficie, rect, t_max, x_max, v_max, pos_mouse=(0, 0)):
    pygame.draw.rect(superficie, FONDO_PANEL, rect, border_radius=6)
    pygame.draw.rect(superficie, BORDE_PANEL, rect, 1, border_radius=6)
    dibujar_esquinas_hud(superficie, rect, CYAN_HUD, tam=10, grosor=2)

    lbl_tit = fuente_subtitulo.render(
        "📊 MACRO-GRÁFICA UNIFICADA: FUSIÓN MULTIVARIABLE Y TELEMETRÍA TOTAL EN TIEMPO REAL", True, AMARILLO_TRAZO)
    superficie.blit(lbl_tit, (rect.x + 12, rect.y + 8))

    mx, my, mb, mr = 60, 36, 30, 20
    g_rect = pygame.Rect(rect.x + mx, rect.y + my, rect.width - mx - mr, rect.height - my - mb)

    surf_alpha = pygame.Surface((g_rect.width, g_rect.height), pygame.SRCALPHA)
    px_ts = int((t_s / t_max) * g_rect.width)
    px_tp = int(((t_s + t_p) / t_max) * g_rect.width)
    px_tot = int((t_total / t_max) * g_rect.width)

    pygame.draw.rect(surf_alpha, (100, 110, 130, 25), (0, 0, px_ts, g_rect.height))
    pygame.draw.rect(surf_alpha, (255, 140, 0, 35), (px_ts, 0, max(0, px_tp - px_ts), g_rect.height))
    pygame.draw.rect(surf_alpha, (255, 30, 86, 25), (px_tp, 0, max(0, px_tot - px_tp), g_rect.height))
    superficie.blit(surf_alpha, (g_rect.x, g_rect.y))

    lbl_f1 = fuente_hud.render("FASE 1: BODEGA", True, GRIS_TEXTO)
    lbl_f2 = fuente_hud.render("FASE 2: PROPULSIÓN", True, NARANJA_PROP)
    lbl_f3 = fuente_hud.render("FASE 3: CRUCERO", True, ROJO_ALERTA)
    superficie.blit(lbl_f1, (g_rect.x + 5, g_rect.y + 4))
    if px_tp > px_ts: superficie.blit(lbl_f2, (g_rect.x + px_ts + 8, g_rect.y + 4))
    if px_tot > px_tp: superficie.blit(lbl_f3, (g_rect.x + px_tp + 8, g_rect.y + 4))

    for i in range(9):
        t_val = (t_max / 8) * i
        px = g_rect.x + int((g_rect.width / 8) * i)
        pygame.draw.line(superficie, GRIS_GRID, (px, g_rect.y), (px, g_rect.bottom), 1)
        lbl_num = fuente_hud.render(f"{t_val:.1f}s", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (px - lbl_num.get_width() // 2, g_rect.bottom + 4))

    for i in range(5):
        pct = (100 // 4) * i
        py = g_rect.bottom - int((g_rect.height / 4) * i)
        pygame.draw.line(superficie, GRIS_GRID, (g_rect.x, py), (g_rect.right, py), 1)
        lbl_num = fuente_hud.render(f"{pct}%", True, GRIS_TEXTO)
        superficie.blit(lbl_num, (g_rect.x - lbl_num.get_width() - 6, py - 6))

    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.bottom), (g_rect.right, g_rect.bottom), 2)
    pygame.draw.line(superficie, BORDE_PANEL, (g_rect.x, g_rect.y), (g_rect.x, g_rect.bottom), 2)

    def t2px(t_val):
        return int(g_rect.x + max(0.0, min(1.0, t_val / t_max)) * g_rect.width)

    if len(sim.hist_x_m) >= 2:
        pts_xm = [(t2px(vt), int(g_rect.bottom - (vx / x_max) * g_rect.height)) for vt, vx, _ in sim.hist_x_m]
        pygame.draw.lines(superficie, CYAN_HUD, False, pts_xm, 2)

    if len(sim.hist_y_m) >= 2 and len(sim.hist_x_m) >= 2:
        pts_ym = []
        for (vt, _, _), vy in zip(sim.hist_x_m, sim.hist_y_m):
            norm_y = (vy - 1000.0) / 3000.0
            pts_ym.append((t2px(vt), int(g_rect.bottom - max(0.0, min(1.0, norm_y)) * g_rect.height)))
        pygame.draw.lines(superficie, VERDE_RADAR, False, pts_ym, 2)

    if len(sim.hist_v_m) >= 2:
        pts_vm = [(t2px(vt), int(g_rect.bottom - max(0.0, min(1.0, vv / v_max)) * g_rect.height)) for vt, vv in
                  sim.hist_v_m]
        pygame.draw.lines(superficie, AMARILLO_TRAZO, False, pts_vm, 2)

    if len(sim.hist_D_rel) >= 2:
        pts_dr = [(t2px(vt), int(g_rect.bottom - max(0.0, min(1.0, vd / D_inicial)) * g_rect.height)) for vt, vd in
                  sim.hist_D_rel]
        pygame.draw.lines(superficie, NARANJA_PROP, False, pts_dr, 2)

    if g_rect.collidepoint(pos_mouse):
        mx_rel = pos_mouse[0] - g_rect.x
        t_h = max(0.0, min(t_max, (mx_rel / g_rect.width) * t_max))
        pygame.draw.line(superficie, BLANCO_TEXTO, (pos_mouse[0], g_rect.y), (pos_mouse[0], g_rect.bottom), 1)
        lbl_h = fuente_hud_bold.render(f"Tiempo Inspector: {t_h:.2f} s", True, BLANCO_TEXTO)
        superficie.blit(lbl_h, (pos_mouse[0] + 8, g_rect.y + 20))

    if sim.impacto_confirmado:
        x_suelta = v_A_ms * t_s
        rect_reporte = pygame.Rect(g_rect.x + 15, g_rect.y + 22, 360, 160)

        pygame.draw.rect(superficie, FONDO_PANEL, rect_reporte, border_radius=6)
        pygame.draw.rect(superficie, VERDE_RADAR, rect_reporte, 2, border_radius=6)

        tit_rep = fuente_subtitulo.render("🎯 RESULTADOS FINALES DE TELEMETRÍA (IMPACTO)", True, VERDE_RADAR)
        superficie.blit(tit_rep, (rect_reporte.x + 10, rect_reporte.y + 8))

        err_wt = ((wt_data['tvuelo'] - t_vuelo) / t_vuelo) * 100
        lineas_rep = [
            f"a) Tiempo Vuelo Misil (tvuelo) : {t_vuelo:.2f} s (WT: {wt_data['tvuelo']:.2f}s)",
            f"b) Distancia Horizontal Misil  : {dist_misil_total:.0f} m (7.00 km)",
            f"Velocidad de Impacto (vmax)    : {v_max_misil:.1f} m/s",
            f"Posición Impacto X (Global)    : {x_impacto:.0f} m",
            f"Separación al Disparo (ds)     : {d_s:.0f} m",
            f"Error Relativo vs WT           : {err_wt:+.2f} %"
        ]

        for idx, lin in enumerate(lineas_rep):
            col_txt = AMARILLO_TRAZO if ("a)" in lin or "b)" in lin) else BLANCO_TEXTO
            t_surf = fuente_hud_bold.render(lin, True, col_txt)
            superficie.blit(t_surf, (rect_reporte.x + 10, rect_reporte.y + 30 + idx * 20))

    dibujar_leyenda(superficie, pygame.Rect(g_rect.right - 175, g_rect.y + 8, 170, 85), [
        (CYAN_HUD, "Posición xm(t)"),
        (VERDE_RADAR, "Altitud ym(t)"),
        (AMARILLO_TRAZO, "Velocidad vm(t)"),
        (NARANJA_PROP, "Distancia Drel(t)")
    ])


# --- 5. BUCLE PRINCIPAL DE EJECUCIÓN ---
ejecutando = True

while ejecutando:
    dt = (reloj.tick(60) / 1000.0) * velocidad_sim
    pos_mouse = pygame.mouse.get_pos()

    rect_2d = pygame.Rect(20, 20, 760, 540)
    rect_eq = pygame.Rect(800, 20, 660, 540)
    rect_gr1 = pygame.Rect(20, 580, 470, 340)
    rect_gr2 = pygame.Rect(505, 580, 470, 340)
    rect_gr3 = pygame.Rect(990, 580, 470, 340)
    rect_fusion = pygame.Rect(20, 580, 1440, 340)

    t1_rect = pygame.Rect(rect_eq.x + 15, rect_eq.y + 25, 630, 130)

    rect_in_D0 = pygame.Rect(t1_rect.x + 145, t1_rect.y + 26, 75, 22)
    rect_in_vA = pygame.Rect(t1_rect.x + 505, t1_rect.y + 26, 75, 22)
    rect_in_vB = pygame.Rect(t1_rect.x + 145, t1_rect.y + 56, 75, 22)
    rect_in_ts = pygame.Rect(t1_rect.x + 505, t1_rect.y + 56, 75, 22)
    rect_in_tp = pygame.Rect(t1_rect.x + 145, t1_rect.y + 86, 75, 22)
    rect_in_am = pygame.Rect(t1_rect.x + 505, t1_rect.y + 86, 75, 22)

    # Botones de control
    rect_btn_iniciar = pygame.Rect(rect_2d.x + 310, rect_2d.y + 8, 80, 22)
    rect_btn_pausa = pygame.Rect(rect_2d.x + 396, rect_2d.y + 8, 80, 22)
    rect_btn_reiniciar = pygame.Rect(rect_2d.x + 482, rect_2d.y + 8, 95, 22)
    rect_btn_fusion = pygame.Rect(rect_2d.x + 583, rect_2d.y + 8, 160, 22)

    rect_btn_spd1 = pygame.Rect(rect_2d.x + 160, rect_2d.y + 8, 35, 22)
    rect_btn_spd2 = pygame.Rect(rect_2d.x + 200, rect_2d.y + 8, 35, 22)
    rect_btn_spd4 = pygame.Rect(rect_2d.x + 240, rect_2d.y + 8, 35, 22)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if rect_btn_iniciar.collidepoint(evento.pos) and not sim.simulacion_iniciada:
                sim.simulacion_iniciada = True
                sim.en_pausa = False
            elif rect_btn_pausa.collidepoint(evento.pos) and sim.simulacion_iniciada:
                sim.en_pausa = not sim.en_pausa
            elif rect_btn_reiniciar.collidepoint(evento.pos):
                sim.simulacion_iniciada = False
                sim.en_pausa = False
                sim.reiniciar()
            elif rect_btn_fusion.collidepoint(evento.pos):
                modo_grafico_fusionado = not modo_grafico_fusionado
            elif rect_btn_spd1.collidepoint(evento.pos):
                velocidad_sim = 1.0
            elif rect_btn_spd2.collidepoint(evento.pos):
                velocidad_sim = 2.0
            elif rect_btn_spd4.collidepoint(evento.pos):
                velocidad_sim = 4.0
            elif not sim.simulacion_iniciada:
                if rect_in_D0.collidepoint(evento.pos): campo_activo = 0
                elif rect_in_vA.collidepoint(evento.pos): campo_activo = 1
                elif rect_in_vB.collidepoint(evento.pos): campo_activo = 2
                elif rect_in_ts.collidepoint(evento.pos): campo_activo = 3
                elif rect_in_tp.collidepoint(evento.pos): campo_activo = 4
                elif rect_in_am.collidepoint(evento.pos): campo_activo = 5
                else: campo_activo = None

        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_r:
                sim.simulacion_iniciada = False
                sim.en_pausa = False
                sim.reiniciar()
            elif evento.key == pygame.K_f:
                modo_grafico_fusionado = not modo_grafico_fusionado
            elif evento.key == pygame.K_SPACE and sim.simulacion_iniciada:
                sim.en_pausa = not sim.en_pausa
            elif campo_activo is not None and not sim.simulacion_iniciada:
                if evento.key == pygame.K_BACKSPACE:
                    if campo_activo == 0: str_D0 = str_D0[:-1]
                    elif campo_activo == 1: str_vA_kmh = str_vA_kmh[:-1]
                    elif campo_activo == 2: str_vB_kmh = str_vB_kmh[:-1]
                    elif campo_activo == 3: str_ts = str_ts[:-1]
                    elif campo_activo == 4: str_tp = str_tp[:-1]
                    elif campo_activo == 5: str_am = str_am[:-1]
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    campo_activo = None
                elif evento.unicode in "0123456789.":
                    if campo_activo == 0 and len(str_D0) < 6: str_D0 += evento.unicode
                    elif campo_activo == 1 and len(str_vA_kmh) < 6: str_vA_kmh += evento.unicode
                    elif campo_activo == 2 and len(str_vB_kmh) < 6: str_vB_kmh += evento.unicode
                    elif campo_activo == 3 and len(str_ts) < 6: str_ts += evento.unicode
                    elif campo_activo == 4 and len(str_tp) < 6: str_tp += evento.unicode
                    elif campo_activo == 5 and len(str_am) < 6: str_am += evento.unicode
                actualizar_parametros()
                sim.reiniciar()

    # ACTUALIZACIÓN FÍSICA Y CINEMÁTICA
    if sim.simulacion_iniciada and not sim.en_pausa and not sim.impacto_confirmado:
        sim.t += dt
        if sim.t >= t_total:
            sim.t = t_total
            sim.impacto_confirmado = True
            for _ in range(50):
                sim.particulas.append(ParticulaExplosion(x_impacto, h_cota))

        sim.x_A = v_A_ms * sim.t
        sim.x_B = D_inicial - v_B_ms * sim.t

        if sim.t < t_s:
            sim.x_m = sim.x_A
            sim.v_m = v_A_ms
            sim.y_m = h_cota
            sim.fase_misil = "BODEGA"
        elif sim.t <= t_s + t_p:
            tau = sim.t - t_s
            sim.x_m = (v_A_ms * t_s) + v_A_ms * tau + 0.5 * a_m * (tau ** 2)
            sim.v_m = v_A_ms + a_m * tau
            sim.y_m = calcular_altitud_loft(sim.x_m, h_loft_real)
            sim.fase_misil = "PROPULSION"
        else:
            tau_c = sim.t - t_s - t_p
            x_end_prop = (v_A_ms * t_s) + v_A_ms * t_p + 0.5 * a_m * (t_p ** 2)
            sim.x_m = x_end_prop + v_max_misil * tau_c
            sim.v_m = v_max_misil
            sim.y_m = calcular_altitud_loft(sim.x_m, h_loft_real)
            sim.fase_misil = "CRUCERO"

        D_relativa = max(0.0, sim.x_B - sim.x_m)

        sim.hist_x_A.append((sim.t, sim.x_A))
        sim.hist_x_B.append((sim.t, sim.x_B))

        if sim.t >= t_s:
            sim.hist_x_m.append((sim.t, sim.x_m, sim.fase_misil))
            sim.hist_y_m.append(sim.y_m)

        sim.hist_v_m.append((sim.t, sim.v_m))
        sim.hist_D_rel.append((sim.t, D_relativa))

    for p in sim.particulas: p.actualizar(dt)
    sim.particulas = [p for p in sim.particulas if p.vida > 0]

    # RENDERIZADO GENERAL
    pantalla.fill(FONDO_APP)

    # 1. ESCENA TÁCTICA 2D
    dibujar_contenedor(pantalla, rect_2d, "VISTA TÁCTICA 2D - INTERCEPCIÓN AAM DIRECTA (h=3000m)", CYAN_HUD)

    def m2px(x_m):
        return int(rect_2d.x + 35 + x_m * ESCALA_X)

    def m2py_2d(x_m):
        y_loft_2d = calcular_altitud_loft(x_m, h_loft_2d)
        norm = (y_loft_2d - h_cota) / 100.0
        return int(rect_2d.centery - norm * 60)

    y_suelo_px = m2py_2d(0.0)
    for grid_x_m in range(0, int(D_inicial) + 1000, 2000):
        px_g = m2px(grid_x_m)
        if rect_2d.x + 35 <= px_g <= rect_2d.x + 35 + ANCHO_UTIL_2D:
            pygame.draw.line(pantalla, GRIS_GRID, (px_g, rect_2d.y + 35), (px_g, rect_2d.bottom - 15), 1)
            lbl_gx = fuente_hud.render(f"{grid_x_m}m", True, GRIS_GRID_LIGHT)
            pantalla.blit(lbl_gx, (px_g - lbl_gx.get_width() // 2, rect_2d.bottom - 16))

    pygame.draw.line(pantalla, BORDE_PANEL, (rect_2d.x + 35, y_suelo_px), (rect_2d.x + 35 + ANCHO_UTIL_2D, y_suelo_px), 1)

    ax_px, ay_px = m2px(sim.x_A), y_suelo_px
    bx_px, by_px = m2px(sim.x_B), y_suelo_px
    mx_px, my_px = m2px(sim.x_m), m2py_2d(sim.x_m)

    if len(sim.hist_x_m) >= 2:
        pts_traza_2d = [(m2px(xm), m2py_2d(xm)) for _, xm, _ in sim.hist_x_m]
        if len(pts_traza_2d) >= 2:
            pygame.draw.lines(pantalla, NARANJA_PROP, False, pts_traza_2d, 2)

    dibujar_caza_eurofighter(pantalla, ax_px, ay_px)
    dibujar_blanco_hostil(pantalla, bx_px, by_px)

    if not sim.impacto_confirmado:
        pos_inicio_d = mx_px if sim.t >= t_s else ax_px
        pygame.draw.line(pantalla, CYAN_HUD, (pos_inicio_d, y_suelo_px - 45), (bx_px, y_suelo_px - 45), 1)
        pygame.draw.line(pantalla, CYAN_HUD, (pos_inicio_d, y_suelo_px - 50), (pos_inicio_d, y_suelo_px - 40), 1)
        pygame.draw.line(pantalla, CYAN_HUD, (bx_px, y_suelo_px - 50), (bx_px, y_suelo_px - 40), 1)
        lbl_drel = fuente_hud_bold.render(f"D_rel: {abs(sim.x_B - sim.x_m):.0f} m", True, CYAN_HUD)
        pantalla.blit(lbl_drel, ((pos_inicio_d + bx_px) // 2 - lbl_drel.get_width() // 2, y_suelo_px - 60))

    ang_misil = 0.0
    if len(sim.hist_x_m) >= 2 and sim.t >= t_s:
        dx_p = sim.hist_x_m[-1][1] - sim.hist_x_m[-2][1]
        dy_p = m2py_2d(sim.hist_x_m[-1][1]) - m2py_2d(sim.hist_x_m[-2][1])
        if dx_p != 0: ang_misil = -math.degrees(math.atan2(dy_p, dx_p))

    col_misil = GRIS_TEXTO if sim.fase_misil == "BODEGA" else (
        NARANJA_PROP if sim.fase_misil == "PROPULSION" else ROJO_ALERTA)
    dibujar_misil_aim120(pantalla, mx_px, my_px, col_misil, ang_grados=ang_misil)

    if sim.impacto_confirmado:
        for p in sim.particulas:
            px_part = rect_2d.x + 35 + p.x * ESCALA_X
            p.dibujar(pantalla)

    # Botones de Control
    for btn, txt, val in [(rect_btn_spd1, "1x", 1.0), (rect_btn_spd2, "2x", 2.0), (rect_btn_spd4, "4x", 4.0)]:
        col_b = AMARILLO_TRAZO if velocidad_sim == val else GRIS_TEXTO
        pygame.draw.rect(pantalla, FONDO_TARJETA, btn, border_radius=3)
        pygame.draw.rect(pantalla, col_b, btn, 1, border_radius=3)
        pantalla.blit(fuente_hud_bold.render(txt, True, col_b), (btn.x + 8, btn.y + 4))

    pygame.draw.rect(pantalla, FONDO_TARJETA, rect_btn_iniciar, border_radius=4)
    pygame.draw.rect(pantalla, VERDE_RADAR if not sim.simulacion_iniciada else GRIS_TEXTO, rect_btn_iniciar, 1, border_radius=4)
    pantalla.blit(fuente_hud_bold.render("▶ INICIAR", True, VERDE_RADAR if not sim.simulacion_iniciada else GRIS_TEXTO), (rect_btn_iniciar.x + 8, rect_btn_iniciar.y + 4))

    pygame.draw.rect(pantalla, FONDO_TARJETA, rect_btn_pausa, border_radius=4)
    pygame.draw.rect(pantalla, CYAN_HUD if sim.simulacion_iniciada else GRIS_TEXTO, rect_btn_pausa, 1, border_radius=4)
    pantalla.blit(fuente_hud_bold.render("⏸ PAUSA" if not sim.en_pausa else "▶ SEGUIR", True, CYAN_HUD if sim.simulacion_iniciada else GRIS_TEXTO), (rect_btn_pausa.x + 8, rect_btn_pausa.y + 4))

    pygame.draw.rect(pantalla, FONDO_TARJETA, rect_btn_reiniciar, border_radius=4)
    pygame.draw.rect(pantalla, ROJO_ALERTA, rect_btn_reiniciar, 1, border_radius=4)
    pantalla.blit(fuente_hud_bold.render("R - RESET", True, BLANCO_TEXTO), (rect_btn_reiniciar.x + 8, rect_btn_reiniciar.y + 4))

    col_fus = AMARILLO_TRAZO if modo_grafico_fusionado else VERDE_RADAR
    pygame.draw.rect(pantalla, FONDO_TARJETA, rect_btn_fusion, border_radius=4)
    pygame.draw.rect(pantalla, col_fus, rect_btn_fusion, 1, border_radius=4)
    pantalla.blit(fuente_hud_bold.render("⚡ FUSIÓN TELEMÉTRICA (F)", True, col_fus), (rect_btn_fusion.x + 6, rect_btn_fusion.y + 4))

    # Panel Telemetría
    dibujar_contenedor(pantalla, rect_eq, "PANEL DE TELEMETRÍA & PARÁMETROS DEL ESCENARIO", CYAN_HUD)

    dibujar_tarjeta_mfd(pantalla, t1_rect, "1. PARÁMETROS DE ENTRADA CONFIGURABLES")
    pantalla.blit(fuente_hud.render("Distancia D0 (m):", True, GRIS_TEXTO), (t1_rect.x + 10, t1_rect.y + 28))
    dibujar_input_box_alineado(pantalla, rect_in_D0, str_D0, campo_activo == 0)

    pantalla.blit(fuente_hud.render("Vel. Interceptor A (km/h):", True, GRIS_TEXTO), (t1_rect.x + 320, t1_rect.y + 28))
    dibujar_input_box_alineado(pantalla, rect_in_vA, str_vA_kmh, campo_activo == 1)

    pantalla.blit(fuente_hud.render("Vel. Blanco B (km/h):", True, GRIS_TEXTO), (t1_rect.x + 10, t1_rect.y + 58))
    dibujar_input_box_alineado(pantalla, rect_in_vB, str_vB_kmh, campo_activo == 2)

    pantalla.blit(fuente_hud.render("Retardo FCS ts (s):", True, GRIS_TEXTO), (t1_rect.x + 320, t1_rect.y + 58))
    dibujar_input_box_alineado(pantalla, rect_in_ts, str_ts, campo_activo == 3)

    pantalla.blit(fuente_hud.render("Tiempo Prop. tp (s):", True, GRIS_TEXTO), (t1_rect.x + 10, t1_rect.y + 88))
    dibujar_input_box_alineado(pantalla, rect_in_tp, str_tp, campo_activo == 4)

    pantalla.blit(fuente_hud.render("Acel. Misil am (m/s²):", True, GRIS_TEXTO), (t1_rect.x + 320, t1_rect.y + 88))
    dibujar_input_box_alineado(pantalla, rect_in_am, str_am, campo_activo == 5)

    # Tarjeta 2: Tabla de Validación
    t2_rect = pygame.Rect(rect_eq.x + 15, rect_eq.y + 165, 630, 155)
    dibujar_tarjeta_mfd(pantalla, t2_rect, "2. VALIDACIÓN TELEMÉTRICA: TEÓRICO VS. WAR THUNDER")

    y_t2 = t2_rect.y + 24
    pantalla.blit(fuente_hud_bold.render("Variable", True, CYAN_HUD), (t2_rect.x + 10, y_t2))
    pantalla.blit(fuente_hud_bold.render("Teórico", True, BLANCO_TEXTO), (t2_rect.x + 230, y_t2))
    pantalla.blit(fuente_hud_bold.render("War Thunder", True, VERDE_RADAR), (t2_rect.x + 350, y_t2))
    pantalla.blit(fuente_hud_bold.render("Error Rel.", True, AMARILLO_TRAZO), (t2_rect.x + 490, y_t2))
    pygame.draw.line(pantalla, BORDE_PANEL, (t2_rect.x + 10, y_t2 + 15), (t2_rect.right - 10, y_t2 + 15), 1)

    x_suelta_m = v_A_ms * t_s

    filas_wt = [
        ("a) Tiempo Vuelo Misil (tvuelo)", f"{t_vuelo:.2f} s", f"{wt_data['tvuelo']:.2f} s",
         f"{((wt_data['tvuelo'] - t_vuelo) / t_vuelo) * 100:+.2f}%"),
        ("b) Recorrido Misil (Δx_total)", f"{dist_misil_total:.0f} m", f"{wt_data['dist_misil']:.0f} m",
         f"{((wt_data['dist_misil'] - dist_misil_total) / dist_misil_total) * 100:+.2f}%"),
        ("Velocidad Máx. (vmax)", f"{v_max_misil:.1f} m/s", f"{wt_data['vmax']:.1f} m/s",
         f"{((wt_data['vmax'] - v_max_misil) / v_max_misil) * 100:+.2f}%"),
        ("Punto de Impacto (ximp)", f"{x_impacto:.0f} m", f"{wt_data['ximp']:.0f} m",
         f"{((wt_data['ximp'] - x_impacto) / x_impacto) * 100:+.2f}%")
    ]

    for idx, (v_nom, v_teo, v_wt, v_err) in enumerate(filas_wt):
        row_y = y_t2 + 20 + idx * 22
        pantalla.blit(fuente_hud.render(v_nom, True, AMARILLO_TRAZO if ("a)" in v_nom or "b)" in v_nom) else GRIS_TEXTO), (t2_rect.x + 10, row_y))
        pantalla.blit(fuente_hud.render(v_teo, True, BLANCO_TEXTO), (t2_rect.x + 230, row_y))
        pantalla.blit(fuente_hud.render(v_wt, True, VERDE_RADAR), (t2_rect.x + 350, row_y))

        col_err = VERDE_RADAR if abs(float(v_err.replace('%', ''))) < 2.0 else AMARILLO_TRAZO
        s_err = fuente_hud_bold.render(v_err, True, col_err)
        badge_rect = pygame.Rect(t2_rect.x + 485, row_y - 1, 75, 17)
        pygame.draw.rect(pantalla, FONDO_PANEL, badge_rect, border_radius=3)
        pygame.draw.rect(pantalla, col_err, badge_rect, 1, border_radius=3)
        pantalla.blit(s_err, (badge_rect.x + 6, badge_rect.y + 1))

    # Tarjeta 3: Respuestas del Enunciado e Indicadores Dinámicos
    t3_rect = pygame.Rect(rect_eq.x + 15, rect_eq.y + 330, 630, 190)
    dibujar_tarjeta_mfd(pantalla, t3_rect, "3. ESTADO DINÁMICO & INDICADOR DE FASES")

    w_fase = 195
    fases_info = [("1. BODEGA (ts)", t_s), ("2. PROPULSIÓN (tp)", t_p), ("3. CRUCERO (tc)", t_c)]
    for idx, (nom_f, dur_f) in enumerate(fases_info):
        bx_f = t3_rect.x + 15 + idx * (w_fase + 10)
        by_f = t3_rect.y + 26
        rect_f = pygame.Rect(bx_f, by_f, w_fase, 24)

        activo = (idx == 0 and sim.fase_misil == "BODEGA") or \
                 (idx == 1 and sim.fase_misil == "PROPULSION") or \
                 (idx == 2 and sim.fase_misil == "CRUCERO")

        col_f = AMARILLO_TRAZO if (activo and sim.simulacion_iniciada) else (
            VERDE_RADAR if sim.impacto_confirmado else BORDE_PANEL)
        pygame.draw.rect(pantalla, FONDO_PANEL, rect_f, border_radius=4)
        pygame.draw.rect(pantalla, col_f, rect_f, 1 if not activo else 2, border_radius=4)

        lbl_f = fuente_hud_bold.render(nom_f, True, BLANCO_TEXTO if activo else GRIS_TEXTO)
        pantalla.blit(lbl_f, (rect_f.x + 10, rect_f.y + 5))

    st_txt = "EN ESPERA - PRESIONAR [INICIAR]" if not sim.simulacion_iniciada else (
        "¡IMPACTO CONFIRMADO EN PUNTO DE INTERCEPCIÓN!" if sim.impacto_confirmado else f"FASE ACTUAL: {sim.fase_misil}"
    )
    col_st = VERDE_RADAR if sim.impacto_confirmado else CYAN_HUD
    pantalla.blit(fuente_alerta.render(st_txt, True, col_st), (t3_rect.x + 15, t3_rect.y + 60))

    dist_misil_actual = max(0.0, sim.x_m - x_suelta_m) if sim.t >= t_s else 0.0
    pantalla.blit(fuente_hud_bold.render(f"Tiempo Simulación (t)  : {sim.t:.2f} s  |  Tiempo Total: {t_total:.2f} s", True, BLANCO_TEXTO), (t3_rect.x + 15, t3_rect.y + 90))
    pantalla.blit(fuente_hud_bold.render(f"a) Tiempo Vuelo Misil : {max(0.0, sim.t - t_s):.2f} s  (Final: {t_vuelo:.2f} s)", True, AMARILLO_TRAZO), (t3_rect.x + 15, t3_rect.y + 112))
    pantalla.blit(fuente_hud_bold.render(f"b) Recorrido del Misil : {dist_misil_actual:.1f} m  (Final: {dist_misil_total:.0f} m)", True, CYAN_HUD), (t3_rect.x + 15, t3_rect.y + 134))
    pantalla.blit(fuente_hud_bold.render(f"Posición X Global     : {sim.x_m:.1f} m  |  Velocidad vm: {sim.v_m:.1f} m/s", True, col_misil), (t3_rect.x + 15, t3_rect.y + 156))

    # Renderizado de Gráficas Inferiores
    if not modo_grafico_fusionado:
        renderizar_grafico_curva_x_vs_t(pantalla, rect_gr1, max(16.0, t_total + 1.0), D_inicial + 500, pos_mouse)
        renderizar_grafico_loft_wt(pantalla, rect_gr2, D_inicial + 500, pos_mouse, y_min=1000.0, y_max=4000.0)
        renderizar_grafico_velocidad_y_distancia(pantalla, rect_gr3, max(16.0, t_total + 1.0), v_max_misil + 100, D_inicial, pos_mouse)
    else:
        renderizar_grafico_unificado(pantalla, rect_fusion, max(16.0, t_total + 1.0), D_inicial + 500, v_max_misil + 100, pos_mouse)

    pygame.display.flip()

pygame.quit()
sys.exit()