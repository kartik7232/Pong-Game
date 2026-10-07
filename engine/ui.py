"""
===============================================================================
PONG GAME ENGINE - UI & MENU NAVIGATION SYSTEM
===============================================================================
Architectural Role: Interactive UI Component with Keyboard & Pointer Support
"""

import pygame
from typing import List, Tuple, Optional, Callable
from engine.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_MENU_SELECTED, COLOR_MENU_UNSELECTED,
    COLOR_MENU_ACCENT, COLOR_TEXT, COLOR_MODAL_BG, COLOR_BG
)


class MenuItem:
    def __init__(self, label: str, action_id: str, tag: str = ""):
        self.label: str = label
        self.action_id: str = action_id
        self.tag: str = tag
        self.rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)


class Menu:
    """
    Menu component providing:
    - Keyboard navigation (Up/Down/Enter)
    - Mouse pointer hover & click
    - Animated / highlighted active selection
    """
    def __init__(
        self,
        items: List[Tuple[str, str]],
        center_x: int = SCREEN_WIDTH // 2,
        start_y: int = 240,
        spacing: int = 48,
        font_size: int = 26
    ):
        self.items: List[MenuItem] = [MenuItem(label, action_id) for label, action_id in items]
        self.selected_index: int = 0
        self.center_x: int = center_x
        self.start_y: int = start_y
        self.spacing: int = spacing
        self.font: pygame.font.Font = pygame.font.SysFont("Consolas", font_size, bold=True)
        self.font_tag: pygame.font.Font = pygame.font.SysFont("Consolas", 14)
        self._update_item_rects()

    def _update_item_rects(self) -> None:
        for i, item in enumerate(self.items):
            rendered = self.font.render(item.label, True, COLOR_TEXT)
            w = max(340, rendered.get_width() + 60)
            h = rendered.get_height() + 16
            x = self.center_x - w // 2
            y = self.start_y + i * self.spacing
            item.rect = pygame.Rect(x, y, w, h)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handles keyboard and mouse events. Returns action_id if an item was activated.
        """
        # Keyboard Navigation
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.items)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.items)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.items[self.selected_index].action_id

        # Mouse Motion: Highlight hovered item
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            for i, item in enumerate(self.items):
                if item.rect.collidepoint(mouse_pos):
                    self.selected_index = i
                    break

        # Mouse Button Click: Activate item if clicked
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for i, item in enumerate(self.items):
                if item.rect.collidepoint(mouse_pos):
                    self.selected_index = i
                    return item.action_id

        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the menu items with active highlight styling."""
        for i, item in enumerate(self.items):
            is_selected = (i == self.selected_index)
            color = COLOR_MENU_SELECTED if is_selected else COLOR_MENU_UNSELECTED

            if is_selected:
                # Highlight card background with subtle glow border
                bg_surface = pygame.Surface((item.rect.width, item.rect.height), pygame.SRCALPHA)
                bg_surface.fill((0, 235, 255, 30))
                surface.blit(bg_surface, item.rect.topleft)
                pygame.draw.rect(surface, COLOR_MENU_SELECTED, item.rect, width=2, border_radius=6)

                # Neon pointer indicators
                prefix = ">  "
                text_surf = self.font.render(f"{prefix}{item.label}", True, COLOR_MENU_SELECTED)
            else:
                text_surf = self.font.render(f"   {item.label}", True, COLOR_MENU_UNSELECTED)

            # Center text inside item rect
            text_rect = text_surf.get_rect(center=item.rect.center)
            surface.blit(text_surf, text_rect)
