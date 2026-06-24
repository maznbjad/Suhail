from __future__ import annotations

from pathlib import Path
import math
import re

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "summary_visuals" / "sprint101"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 760, 320


def esc(text: str) -> str:
    return (str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def base_svg(title: str, accent: str, art: str, formula: str = "", soft: str = "#f4fbff") -> str:
    # Sprint 101 keeps diagrams image-only. Arabic lesson text and formulas stay
    # as live HTML in the app for perfect readability and accessibility.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{soft}"/><stop offset="1" stop-color="#ffffff"/></linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="9" stdDeviation="11" flood-color="#173b62" flood-opacity=".12"/></filter>
      </defs>
      <rect width="760" height="320" rx="34" fill="url(#bg)"/>
      <path d="M0 252 C150 214 270 296 430 246 C570 204 654 230 760 188 L760 320 L0 320Z" fill="{accent}" fill-opacity=".075"/>
      <circle cx="700" cy="55" r="95" fill="{accent}" fill-opacity=".055"/>
      <g transform="translate(45 -5) scale(1.22)" filter="url(#shadow)">{art}</g>
    </svg>'''


def atom_art() -> str:
    rings = ''.join(f'<ellipse cx="245" cy="165" rx="118" ry="44" fill="none" stroke="#2f8ee5" stroke-width="5" transform="rotate({a} 245 165)" opacity=".82"/>' for a in (0,60,120))
    return f'''<g>{rings}<circle cx="245" cy="165" r="39" fill="#3a8bdc"/><circle cx="225" cy="155" r="17" fill="#ef5967"/><circle cx="263" cy="147" r="16" fill="#55c783"/><circle cx="252" cy="184" r="17" fill="#f3b43e"/><circle cx="360" cy="165" r="12" fill="#55c783"/><circle cx="185" cy="68" r="11" fill="#ef5967"/><circle cx="190" cy="255" r="11" fill="#2f8ee5"/></g>'''


def molecule_art(kind: str = 'water') -> str:
    if kind == 'lattice':
        out=[]
        for r in range(4):
            for c in range(5):
                x=120+c*55; y=75+r*55
                col='#2f8ee5' if (r+c)%2==0 else '#55c783'
                out.append(f'<circle cx="{x}" cy="{y}" r="18" fill="{col}"/><circle cx="{x}" cy="{y}" r="8" fill="#fff" fill-opacity=".65"/>')
                if c<4: out.append(f'<path d="M{x+18} {y}H{x+37}" stroke="#8fb6d8" stroke-width="5"/>')
                if r<3: out.append(f'<path d="M{x} {y+18}V{y+37}" stroke="#8fb6d8" stroke-width="5"/>')
        return '<g>'+''.join(out)+'</g>'
    if kind == 'organic':
        return '''<g stroke="#254e76" stroke-width="7" stroke-linecap="round"><path d="M110 178L175 130L245 165L315 115L382 158"/><path d="M175 130L175 62"/><path d="M245 165L248 238"/><path d="M315 115L368 70"/></g><g fill="#55c783" stroke="#fff" stroke-width="5"><circle cx="110" cy="178" r="24"/><circle cx="175" cy="130" r="24"/><circle cx="245" cy="165" r="24"/><circle cx="315" cy="115" r="24"/><circle cx="382" cy="158" r="24"/></g><g fill="#ef5967" stroke="#fff" stroke-width="5"><circle cx="175" cy="62" r="21"/><circle cx="248" cy="238" r="21"/></g><circle cx="368" cy="70" r="20" fill="#2f8ee5" stroke="#fff" stroke-width="5"/>'''
    # water reaction
    return '''<g stroke="#7f9ab4" stroke-width="7" stroke-linecap="round"><path d="M110 160h55M242 160h55M365 160h55"/></g><g><circle cx="95" cy="160" r="25" fill="#eef2f6" stroke="#9aabba" stroke-width="4"/><circle cx="180" cy="160" r="25" fill="#eef2f6" stroke="#9aabba" stroke-width="4"/><circle cx="225" cy="160" r="31" fill="#ef5967" stroke="#c63f50" stroke-width="4"/><circle cx="315" cy="160" r="31" fill="#ef5967" stroke="#c63f50" stroke-width="4"/><circle cx="350" cy="160" r="25" fill="#eef2f6" stroke="#9aabba" stroke-width="4"/><circle cx="435" cy="160" r="25" fill="#eef2f6" stroke="#9aabba" stroke-width="4"/></g><path d="M190 232H380" stroke="#2f8ee5" stroke-width="7" stroke-linecap="round"/><path d="M380 232l-20-13v26z" fill="#2f8ee5"/>'''


def flask_art(liquid='#58c98b') -> str:
    return f'''<g><path d="M205 55h90M230 55v55l-82 126c-17 26 2 48 31 48h143c29 0 48-22 31-48l-82-126V55" fill="#fff" fill-opacity=".82" stroke="#2d6d9e" stroke-width="7" stroke-linejoin="round"/><path d="M185 223h134l29 45c5 8-1 16-12 16H165c-11 0-17-8-12-16z" fill="{liquid}" fill-opacity=".88"/><g fill="#fff" fill-opacity=".74"><circle cx="215" cy="242" r="8"/><circle cx="262" cy="259" r="10"/><circle cx="291" cy="235" r="6"/></g><path d="M230 87h41" stroke="#8fb6d8" stroke-width="5" stroke-linecap="round"/></g>'''


def periodic_art() -> str:
    colors=['#d9efff','#dff7e7','#fff0c8','#f8ddff']
    cells=[]
    labels=['H','C','N','O','Na','Mg','Cl','K','Ca','Fe','Cu','Zn']
    k=0
    for r in range(3):
        for c in range(4):
            x=85+c*78; y=65+r*72
            cells.append(f'<rect x="{x}" y="{y}" width="60" height="56" rx="12" fill="{colors[(r+c)%4]}" stroke="#5b8cb6" stroke-opacity=".35"/><text x="{x+30}" y="{y+37}" text-anchor="middle" font-family="DejaVu Sans" font-weight="700" font-size="22" fill="#173b62">{labels[k]}</text>')
            k+=1
    return '<g>'+''.join(cells)+'</g>'


def orbitals_art() -> str:
    return '''<g transform="translate(80 45)"><path d="M170 115C75 20 40 205 170 115C300 20 265 205 170 115Z" fill="#2f8ee5" fill-opacity=".15" stroke="#2f8ee5" stroke-width="5"/><path d="M170 115C92 52 92 178 170 115C248 52 248 178 170 115Z" fill="#55c783" fill-opacity=".18" stroke="#55c783" stroke-width="5" transform="rotate(60 170 115)"/><circle cx="170" cy="115" r="23" fill="#ef5967"/><circle cx="282" cy="115" r="11" fill="#2f8ee5"/><circle cx="115" cy="40" r="11" fill="#55c783"/></g>'''


def phase_art() -> str:
    return '''<g><rect x="58" y="80" width="112" height="112" rx="20" fill="#cce9ff"/><g fill="#2f8ee5">'''+''.join(f'<circle cx="{82+(i%3)*32}" cy="{104+(i//3)*32}" r="11"/>' for i in range(9))+'''</g><rect x="205" y="80" width="112" height="112" rx="20" fill="#dbf6e7"/><g fill="#55c783">'''+''.join(f'<circle cx="{228+(i%3)*32+(i%2)*6}" cy="{104+(i//3)*32}" r="11"/>' for i in range(9))+'''</g><rect x="352" y="80" width="112" height="112" rx="20" fill="#fff0cf"/><g fill="#f0ad38"><circle cx="385" cy="109" r="11"/><circle cx="438" cy="136" r="11"/><circle cx="392" cy="176" r="11"/><circle cx="453" cy="93" r="11"/></g><path d="M174 136h25M321 136h25" stroke="#173b62" stroke-width="7" stroke-linecap="round"/><path d="M195 125l13 11-13 11M342 125l13 11-13 11" fill="none" stroke="#173b62" stroke-width="5"/></g>'''


def graph_art(kind='energy') -> str:
    if kind=='rate':
        curve='M92 250 C150 247 180 224 220 192 C275 148 325 93 420 70'
        curve2='M92 250 C150 242 190 193 235 130 C290 58 350 50 420 45'
        return f'''<g><path d="M80 42V260H440" fill="none" stroke="#173b62" stroke-width="6"/><path d="{curve}" fill="none" stroke="#2f8ee5" stroke-width="8" stroke-linecap="round"/><path d="{curve2}" fill="none" stroke="#55c783" stroke-width="8" stroke-linecap="round"/><circle cx="322" cy="95" r="9" fill="#55c783"/><circle cx="305" cy="112" r="9" fill="#2f8ee5"/></g>'''
    if kind=='equilibrium':
        return '''<g><path d="M70 50V260H445" fill="none" stroke="#173b62" stroke-width="6"/><path d="M82 85C145 110 180 180 240 190S350 174 435 174" fill="none" stroke="#2f8ee5" stroke-width="8"/><path d="M82 236C145 212 185 170 240 160S350 174 435 174" fill="none" stroke="#55c783" stroke-width="8"/><path d="M263 80h90" stroke="#f0ad38" stroke-width="7" stroke-linecap="round" stroke-dasharray="9 10"/></g>'''
    return '''<g><path d="M75 52V258H445" fill="none" stroke="#173b62" stroke-width="6"/><path d="M85 225C130 218 160 180 196 182C240 185 250 78 315 75C352 73 380 110 435 105" fill="none" stroke="#2f8ee5" stroke-width="9" stroke-linecap="round"/><path d="M75 225H445" stroke="#8fb6d8" stroke-width="3" stroke-dasharray="10 10"/><path d="M315 75V225" stroke="#ef5967" stroke-width="4" stroke-dasharray="8 8"/></g>'''


def projectile_art() -> str:
    return '''<g><path d="M65 260V45M65 260H445" stroke="#173b62" stroke-width="6"/><path d="M65 258C140 88 295 76 430 258" fill="none" stroke="#2f8ee5" stroke-width="8" stroke-dasharray="14 10"/><path d="M65 258L150 150" stroke="#55c783" stroke-width="8"/><path d="M150 150l-8 25-18-14z" fill="#55c783"/><path d="M252 92V258" stroke="#8fa8be" stroke-width="4" stroke-dasharray="9 8"/><path d="M70 285H430" stroke="#55c783" stroke-width="5"/><path d="M70 285l16-9v18zM430 285l-16-9v18z" fill="#55c783"/><text x="160" y="145" font-family="DejaVu Sans" font-size="24" font-weight="700" fill="#173b62">v₀</text><text x="253" y="180" font-family="DejaVu Sans" font-size="24" font-weight="700" fill="#173b62">H</text><text x="250" y="311" font-family="DejaVu Sans" font-size="24" font-weight="700" fill="#173b62">R</text></g>'''


def force_art() -> str:
    return '''<g><rect x="180" y="125" width="125" height="96" rx="16" fill="#dcecff" stroke="#2f8ee5" stroke-width="6"/><path d="M242 122V54M242 224v68M177 173H90M308 173h105" stroke="#173b62" stroke-width="7" stroke-linecap="round"/><path d="M242 54l-12 20h24zM242 292l-12-20h24zM90 173l20-12v24zM413 173l-20-12v24z" fill="#173b62"/><text x="260" y="80" font-family="DejaVu Sans" font-size="23" fill="#173b62">N</text><text x="262" y="284" font-family="DejaVu Sans" font-size="23" fill="#173b62">mg</text><text x="385" y="155" font-family="DejaVu Sans" font-size="23" fill="#173b62">F</text><text x="98" y="155" font-family="DejaVu Sans" font-size="23" fill="#173b62">f</text><path d="M65 230H440" stroke="#8fa8be" stroke-width="5"/></g>'''


def wave_art() -> str:
    points=[]
    for i in range(361):
        x=70+i
        y=165-70*math.sin(i/45*math.pi)
        points.append(f'{x:.1f},{y:.1f}')
    return f'''<g><path d="M60 165H452" stroke="#8fa8be" stroke-width="4" stroke-dasharray="10 8"/><polyline points="{' '.join(points)}" fill="none" stroke="#2f8ee5" stroke-width="9" stroke-linecap="round"/><path d="M117 85V245M297 85V245" stroke="#55c783" stroke-width="4" stroke-dasharray="8 8"/><path d="M117 270H297" stroke="#55c783" stroke-width="5"/><path d="M117 270l14-8v16zM297 270l-14-8v16z" fill="#55c783"/><text x="200" y="306" font-family="DejaVu Sans" font-size="25" font-weight="700" fill="#173b62">λ</text></g>'''


def lens_art() -> str:
    return '''<g><path d="M55 165H450" stroke="#8fa8be" stroke-width="4" stroke-dasharray="10 9"/><path d="M270 55C235 90 235 240 270 275C305 240 305 90 270 55Z" fill="#bce8ff" stroke="#2f8ee5" stroke-width="6"/><path d="M75 105V225" stroke="#173b62" stroke-width="7"/><path d="M75 105l-13 24h26z" fill="#173b62"/><path d="M75 105L270 105L425 165M75 105L270 165L425 225M75 105L270 225L425 165" fill="none" stroke="#f0ad38" stroke-width="5"/><circle cx="190" cy="165" r="7" fill="#173b62"/><circle cx="350" cy="165" r="7" fill="#173b62"/><text x="182" y="195" font-family="DejaVu Sans" font-size="20" fill="#173b62">F</text><text x="342" y="195" font-family="DejaVu Sans" font-size="20" fill="#173b62">F</text></g>'''


def circuit_art(kind='circuit') -> str:
    if kind=='battery':
        return '''<g><rect x="88" y="84" width="90" height="155" rx="22" fill="#e8f3ff" stroke="#2f8ee5" stroke-width="6"/><rect x="112" y="60" width="42" height="26" rx="7" fill="#173b62"/><rect x="215" y="84" width="90" height="155" rx="22" fill="#e5f9ec" stroke="#55c783" stroke-width="6"/><rect x="239" y="60" width="42" height="26" rx="7" fill="#173b62"/><rect x="342" y="84" width="90" height="155" rx="22" fill="#fff0cf" stroke="#f0ad38" stroke-width="6"/><rect x="366" y="60" width="42" height="26" rx="7" fill="#173b62"/><path d="M115 160h36M133 142v36M240 160h40M369 160h36M387 142v36" stroke="#173b62" stroke-width="6" stroke-linecap="round"/></g>'''
    if kind=='electrolysis':
        return '''<g><rect x="100" y="110" width="330" height="145" rx="25" fill="#dff7ff" stroke="#2f8ee5" stroke-width="6"/><path d="M170 55V213M360 55V213" stroke="#173b62" stroke-width="12"/><path d="M170 55H235M295 55H360" stroke="#173b62" stroke-width="7"/><rect x="235" y="35" width="60" height="40" rx="9" fill="#f0ad38"/><g fill="#55c783"><circle cx="160" cy="215" r="8"/><circle cx="185" cy="198" r="7"/><circle cx="350" cy="215" r="8"/><circle cx="375" cy="196" r="7"/></g><path d="M235 55h60" stroke="#fff" stroke-width="5"/></g>'''
    return '''<g><path d="M90 86H180L205 58L255 112L305 58L355 112L385 86H440V238H90Z" fill="none" stroke="#173b62" stroke-width="7" stroke-linejoin="round"/><rect x="70" y="137" width="42" height="50" rx="6" fill="#f0ad38" stroke="#173b62" stroke-width="5"/><path d="M82 124v-18M100 124V92" stroke="#173b62" stroke-width="5"/><path d="M265 238v-44M265 194h60" stroke="#2f8ee5" stroke-width="7"/><circle cx="266" cy="239" r="8" fill="#2f8ee5"/></g>'''


def acid_art() -> str:
    return '''<g><path d="M100 75h95M120 75v45l-50 105c-12 25 3 43 28 43h120c25 0 40-18 28-43l-50-105V75" fill="#fff" stroke="#2f8ee5" stroke-width="6"/><path d="M92 220h132l22 46H70z" fill="#ef5967" fill-opacity=".72"/><text x="158" y="246" text-anchor="middle" font-family="DejaVu Sans" font-size="28" font-weight="700" fill="#fff">H⁺</text><path d="M300 75h95M320 75v45l-50 105c-12 25 3 43 28 43h120c25 0 40-18 28-43l-50-105V75" fill="#fff" stroke="#55c783" stroke-width="6"/><path d="M292 220h132l22 46H270z" fill="#55c783" fill-opacity=".72"/><text x="358" y="246" text-anchor="middle" font-family="DejaVu Sans" font-size="28" font-weight="700" fill="#fff">OH⁻</text><path d="M239 160h61" stroke="#f0ad38" stroke-width="7"/><path d="M294 149l15 11-15 11" fill="none" stroke="#f0ad38" stroke-width="6"/></g>'''


def concentration_art() -> str:
    return '''<g><rect x="65" y="85" width="120" height="165" rx="20" fill="#dff7ff" stroke="#2f8ee5" stroke-width="6"/><rect x="220" y="85" width="120" height="165" rx="20" fill="#dff7e7" stroke="#55c783" stroke-width="6"/><rect x="375" y="85" width="120" height="165" rx="20" fill="#fff0cf" stroke="#f0ad38" stroke-width="6"/><g fill="#2f8ee5">'''+''.join(f'<circle cx="{90+(i%3)*33}" cy="{120+(i//3)*34}" r="8"/>' for i in range(6))+'''</g><g fill="#55c783">'''+''.join(f'<circle cx="{245+(i%3)*33}" cy="{120+(i//3)*34}" r="8"/>' for i in range(9))+'''</g><g fill="#f0ad38">'''+''.join(f'<circle cx="{400+(i%3)*33}" cy="{112+(i//3)*31}" r="8"/>' for i in range(12))+'''</g></g>'''


def visual_art(kind: str) -> str:
    if kind in {'atom','isotopes','nuclear','quantum'}: return atom_art()
    if kind in {'periodic','elements'}: return periodic_art()
    if kind in {'orbitals','electron'}: return orbitals_art()
    if kind in {'ionic','lattice'}: return molecule_art('lattice')
    if kind in {'organic','hydrocarbon','polymer','protein','carbohydrate','lipid','nucleic'}: return molecule_art('organic')
    if kind in {'reaction','equation','stoichiometry','redox'}: return molecule_art('water')
    if kind in {'phase','states','intermolecular','gas'}: return phase_art()
    if kind in {'energy','calorimetry','thermochemical','hess'}: return graph_art('energy')
    if kind in {'rate','collision'}: return graph_art('rate')
    if kind in {'equilibrium'}: return graph_art('equilibrium')
    if kind in {'acid','base','ph','neutralization'}: return acid_art()
    if kind in {'solution','concentration','solubility','colligative','mixture'}: return concentration_art()
    if kind in {'circuit','electrochemical'}: return circuit_art('circuit')
    if kind in {'battery'}: return circuit_art('battery')
    if kind in {'electrolysis'}: return circuit_art('electrolysis')
    if kind in {'projectile'}: return projectile_art()
    if kind in {'force','motion','vector','momentum'}: return force_art()
    if kind in {'wave','sound'}: return wave_art()
    if kind in {'lens','light'}: return lens_art()
    return flask_art()


VISUALS = {
    # Physics reusable visuals
    'phy_measurement': ('القياس والنماذج', '#2f8ee5', 'vector', 'value = number + unit'),
    'phy_motion': ('الحركة والقوى', '#2f8ee5', 'motion', 'F = ma'),
    'phy_projectile': ('الحركة المقذوفة', '#2f8ee5', 'projectile', 'R = v₀² sin(2θ) / g'),
    'phy_momentum': ('الزخم والدفع', '#7258db', 'momentum', 'p = mv'),
    'phy_energy': ('الشغل والطاقة', '#7258db', 'energy', 'KE = ½mv²'),
    'phy_thermal': ('الحرارة والطاقة', '#ef7a45', 'calorimetry', 'Q = mcΔT'),
    'phy_wave': ('الموجات', '#2f8ee5', 'wave', 'v = fλ'),
    'phy_sound': ('الصوت', '#2f8ee5', 'sound', 'v = fλ'),
    'phy_light': ('الضوء', '#f0ad38', 'light', 'n₁sinθ₁ = n₂sinθ₂'),
    'phy_lens': ('العدسات والمرايا', '#2f8ee5', 'lens', '1/f = 1/do + 1/di'),
    'phy_electric': ('الكهرباء', '#2f8ee5', 'circuit', 'V = IR'),
    'phy_magnetic': ('المغناطيسية والحث', '#7258db', 'electrochemical', 'ε = -NΔΦ/Δt'),
    'phy_quantum': ('الكم والذرة', '#7258db', 'quantum', 'E = hf'),
    'phy_nuclear': ('الفيزياء النووية', '#ef5967', 'nuclear', 'E = mc²'),
    # Chemistry visuals
    'chem_lab': ('علم الكيمياء', '#12aeb0', 'lab', ''),
    'chem_matter': ('المادة وخواصها', '#12aeb0', 'states', ''),
    'chem_mixture': ('المخاليط', '#12aeb0', 'mixture', ''),
    'chem_atom_history': ('تطور نموذج الذرة', '#7258db', 'atom', ''),
    'chem_atom': ('بنية الذرة', '#7258db', 'atom', 'A = Z + n'),
    'chem_isotopes': ('النظائر', '#7258db', 'isotopes', 'A = p + n'),
    'chem_nuclear': ('التحلل الإشعاعي', '#ef5967', 'nuclear', 'N = N₀(½)ᵗ/ᵗ½'),
    'chem_equation': ('المعادلات الكيميائية', '#12aeb0', 'equation', '2H₂ + O₂ → 2H₂O'),
    'chem_reactions': ('أنواع التفاعلات', '#12aeb0', 'reaction', 'A + B → AB'),
    'chem_aqueous': ('التفاعلات في المحاليل', '#12aeb0', 'solution', 'AB(aq) + CD(aq)'),
    'chem_mole': ('المول والكتلة', '#55a942', 'stoichiometry', 'n = m / M'),
    'chem_quantum': ('الضوء وطاقة الكم', '#7258db', 'quantum', 'E = hν'),
    'chem_orbitals': ('التوزيع الإلكتروني', '#7258db', 'orbitals', '1s² 2s² 2p⁶'),
    'chem_periodic': ('الجدول الدوري', '#2f8ee5', 'periodic', ''),
    'chem_ions': ('تكوّن الأيونات', '#2f8ee5', 'ionic', 'Na → Na⁺ + e⁻'),
    'chem_ionic': ('الرابطة الأيونية', '#2f8ee5', 'lattice', 'Na⁺Cl⁻'),
    'chem_metallic': ('الرابطة الفلزية', '#2f8ee5', 'lattice', ''),
    'chem_covalent': ('الرابطة التساهمية', '#12aeb0', 'organic', 'H—O—H'),
    'chem_lewis': ('تراكيب لويس', '#12aeb0', 'organic', ''),
    'chem_geometry': ('أشكال الجزيئات', '#12aeb0', 'organic', 'VSEPR'),
    'chem_polarity': ('القطبية', '#12aeb0', 'organic', 'δ⁺ → δ⁻'),
    'chem_stoich': ('الحسابات الكيميائية', '#55a942', 'stoichiometry', 'n = m / M'),
    'chem_limiting': ('المادة المحددة', '#55a942', 'reaction', ''),
    'chem_yield': ('المردود المئوي', '#55a942', 'reaction', '%yield = actual/theoretical ×100'),
    'chem_states': ('حالات المادة', '#2f8ee5', 'states', ''),
    'chem_forces': ('قوى التجاذب', '#2f8ee5', 'intermolecular', ''),
    'chem_phase': ('تغيرات الحالة', '#2f8ee5', 'phase', ''),
    'chem_gas': ('قوانين الغازات', '#2f8ee5', 'gas', 'PV = nRT'),
    'chem_energy': ('الطاقة والتغيرات', '#ef7a45', 'energy', 'ΔE = q + w'),
    'chem_heat': ('الحرارة', '#ef7a45', 'calorimetry', 'q = mcΔT'),
    'chem_thermo': ('الكيمياء الحرارية', '#ef7a45', 'thermochemical', 'ΔH = Hproducts − Hreactants'),
    'chem_hess': ('قانون هس', '#ef7a45', 'hess', 'ΔHtotal = ΣΔH'),
    'chem_collision': ('نظرية التصادم', '#12aeb0', 'collision', ''),
    'chem_rate': ('سرعة التفاعل', '#12aeb0', 'rate', 'rate = Δ[ ] / Δt'),
    'chem_equilibrium': ('الاتزان الكيميائي', '#7258db', 'equilibrium', 'Kc = products/reactants'),
    'chem_hydrocarbon': ('الهيدروكربونات', '#55a942', 'hydrocarbon', 'CₙH₂ₙ₊₂'),
    'chem_organic': ('المركبات العضوية', '#55a942', 'organic', ''),
    'chem_polymer': ('البوليمرات', '#55a942', 'polymer', '(—CH₂—CH₂—)ₙ'),
    'chem_protein': ('البروتينات', '#55a942', 'protein', ''),
    'chem_carbohydrate': ('الكربوهيدرات', '#55a942', 'carbohydrate', 'C₆H₁₂O₆'),
    'chem_lipid': ('الليبيدات', '#55a942', 'lipid', ''),
    'chem_nucleic': ('الأحماض النووية', '#55a942', 'nucleic', 'DNA / RNA'),
    'chem_solution': ('المحاليل', '#12aeb0', 'solution', ''),
    'chem_concentration': ('تركيز المحلول', '#12aeb0', 'concentration', 'M = mol / L'),
    'chem_solubility': ('الذوبان', '#12aeb0', 'solubility', ''),
    'chem_colligative': ('الخواص الجامعة', '#12aeb0', 'colligative', 'ΔTf = iKf m'),
    'chem_acid': ('الأحماض والقواعد', '#ef5967', 'acid', 'HA ⇌ H⁺ + A⁻'),
    'chem_ph': ('الرقم الهيدروجيني', '#ef5967', 'ph', 'pH = −log[H⁺]'),
    'chem_neutralization': ('التعادل', '#ef5967', 'neutralization', 'H⁺ + OH⁻ → H₂O'),
    'chem_redox': ('الأكسدة والاختزال', '#7258db', 'redox', 'Oxidation = loss of e⁻'),
    'chem_electrochemical': ('الخلايا الجلفانية', '#2f8ee5', 'electrochemical', 'E°cell = E°cathode − E°anode'),
    'chem_battery': ('البطاريات', '#2f8ee5', 'battery', ''),
    'chem_electrolysis': ('التحليل الكهربائي', '#2f8ee5', 'electrolysis', ''),
}


def main() -> None:
    for visual_id, (title, accent, kind, formula) in VISUALS.items():
        art = visual_art(kind)
        soft = '#f1fbff' if accent in {'#2f8ee5','#12aeb0'} else '#f8f5ff' if accent=='#7258db' else '#fff8f1'
        svg = base_svg(title, accent, art, formula, soft)
        svg_path = OUT / f'{visual_id}.svg'
        png_path = OUT / f'{visual_id}.png'
        webp_path = OUT / f'{visual_id}.webp'
        svg_path.write_text(svg, encoding='utf-8')
        cairosvg.svg2png(bytestring=svg.encode('utf-8'), write_to=str(png_path), output_width=W, output_height=H)
        with Image.open(png_path) as im:
            im.convert('RGB').save(webp_path, 'WEBP', quality=72, method=6)
        png_path.unlink(missing_ok=True)
    print(f'generated {len(VISUALS)} visuals in {OUT}')


if __name__ == '__main__':
    main()
