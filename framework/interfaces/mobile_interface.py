"""
MobileInterface - Appium driver wrapper with enhanced functionality.

Wraps an Appium WebDriver session with the shared Interface-layer
primitives (finders, waits, interactions, gestures) used across
android/ios/web-context test targets.
"""

import logging
from typing import Any, List, Optional

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.interaction import POINTER_TOUCH
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class MobileInterface:
    DEFAULT_EXPLICIT_WAIT = 20

    def __init__(self, driver: WebDriver, config: dict,
                 logger: logging.Logger, platform: str) -> None:
        self.driver, self.config, self.logger = driver, config, logger
        self.platform = platform.lower()            # "android" | "ios"; else ValueError
        self.explicit_wait = int(config.get("explicit_wait", self.DEFAULT_EXPLICIT_WAIT))

    def find_element(self, by: str, value: str, timeout: Optional[int] = None) -> WebElement:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Element not found: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error finding element: by={by}, value={value}, error={exc}")
            raise

    def find_elements(self, by: str, value: str, timeout: Optional[int] = None) -> List[WebElement]:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_all_elements_located((by, value))
            )
        except TimeoutException:
            self.logger.warning(f"No elements found: by={by}, value={value}, timeout={wait_time}")
            return []
        except WebDriverException as exc:
            self.logger.error(f"Driver error finding elements: by={by}, value={value}, error={exc}")
            raise

    def is_element_present(self, by: str, value: str, timeout: Optional[int] = None) -> bool:
        try:
            self.find_element(by, value, timeout)
            return True
        except TimeoutException:
            self.logger.error(f"Element not present: by={by}, value={value}, timeout={timeout}")
            return False

    def is_element_displayed(self, by: str, value: str, timeout: Optional[int] = None) -> bool:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((by, value))
            )
            return element.is_displayed()
        except TimeoutException:
            self.logger.error(f"Element not displayed: by={by}, value={value}, timeout={wait_time}")
            return False
        except WebDriverException as exc:
            self.logger.error(f"Driver error checking element displayed: by={by}, value={value}, error={exc}")
            raise

    def is_element_clickable(self, by: str, value: str, timeout: Optional[int] = None) -> bool:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable((by, value))
            )
            return True
        except TimeoutException:
            self.logger.error(f"Element not clickable: by={by}, value={value}, timeout={wait_time}")
            return False
        except WebDriverException as exc:
            self.logger.error(f"Driver error checking element clickable: by={by}, value={value}, error={exc}")
            raise

    def wait_for_element_visible(self, by: str, value: str, timeout: Optional[int] = None) -> WebElement:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Element not visible: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error waiting for visibility: by={by}, value={value}, error={exc}")
            raise

    def wait_for_element_invisible(self, by: str, value: str, timeout: Optional[int] = None) -> bool:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.invisibility_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Element still visible: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error waiting for invisibility: by={by}, value={value}, error={exc}")
            raise

    def wait_for_text_in_element(self, by: str, value: str, text: str, timeout: Optional[int] = None) -> bool:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.text_to_be_present_in_element((by, value), text)
            )
        except TimeoutException:
            self.logger.error(f"Text not present in element: by={by}, value={value}, text={text}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error waiting for text: by={by}, value={value}, text={text}, error={exc}")
            raise

    def wait_for_url_contains(self, url_fragment: str, timeout: Optional[int] = None) -> bool:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"wait_for_url_contains is not supported in context={self.driver.current_context}"
            )
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.url_contains(url_fragment)
            )
        except TimeoutException:
            self.logger.error(f"URL does not contain fragment: url_fragment={url_fragment}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error waiting for url: url_fragment={url_fragment}, error={exc}")
            raise

    def click(self, by: str, value: str, timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
        except TimeoutException:
            self.logger.error(f"Element not clickable: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error clicking element: by={by}, value={value}, error={exc}")
            raise

    def type(self, by: str, value: str, text: str, clear_first: bool = True,
             timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            if clear_first:
                element.clear()
            element.send_keys(text)
        except TimeoutException:
            self.logger.error(f"Element not found for type: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error typing text: by={by}, value={value}, text={text}, error={exc}")
            raise

    def execute_script(self, script: str, *args) -> Any:
        try:
            return self.driver.execute_script(script, *args)
        except WebDriverException as exc:
            self.logger.error(f"Driver error executing script: script={script}, error={exc}")
            raise

    def get_text(self, by: str, value: str, timeout: Optional[int] = None) -> str:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return element.text
        except TimeoutException:
            self.logger.error(f"Element not found for get_text: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting text: by={by}, value={value}, error={exc}")
            raise

    def get_attribute(self, by: str, value: str, attribute: str,
                       timeout: Optional[int] = None) -> Optional[str]:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return element.get_attribute(attribute)
        except TimeoutException:
            self.logger.error(f"Element not found for get_attribute: by={by}, value={value}, attribute={attribute}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting attribute: by={by}, value={value}, attribute={attribute}, error={exc}")
            raise

    def get_page_source(self) -> str:
        try:
            return self.driver.page_source
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting page source: error={exc}")
            raise

    def take_screenshot(self, file_path: str) -> str:
        try:
            self.driver.save_screenshot(file_path)
            return file_path
        except WebDriverException as exc:
            self.logger.error(f"Driver error taking screenshot: file_path={file_path}, error={exc}")
            raise

    def navigate_to(self, url: str) -> None:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"navigate_to is not supported in context={self.driver.current_context}"
            )
        try:
            self.driver.get(url)
        except WebDriverException as exc:
            self.logger.error(f"Driver error navigating: url={url}, error={exc}")
            raise

    def refresh_page(self) -> None:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"refresh_page is not supported in context={self.driver.current_context}"
            )
        try:
            self.driver.refresh()
        except WebDriverException as exc:
            self.logger.error(f"Driver error refreshing page: error={exc}")
            raise

    def go_back(self) -> None:
        try:
            self.driver.back()
        except WebDriverException as exc:
            self.logger.error(f"Driver error going back: error={exc}")
            raise

    def go_forward(self) -> None:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"go_forward is not supported in context={self.driver.current_context}"
            )
        try:
            self.driver.forward()
        except WebDriverException as exc:
            self.logger.error(f"Driver error going forward: error={exc}")
            raise

    def get_current_url(self) -> str:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"get_current_url is not supported in context={self.driver.current_context}"
            )
        try:
            return self.driver.current_url
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting current url: error={exc}")
            raise

    def get_page_title(self) -> str:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"get_page_title is not supported in context={self.driver.current_context}"
            )
        try:
            return self.driver.title
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting page title: error={exc}")
            raise

    def select_by_text(self, by: str, value: str, text: str,
                        timeout: Optional[int] = None) -> None:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"select_by_text is not supported in context={self.driver.current_context}"
            )
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            Select(element).select_by_visible_text(text)
        except TimeoutException:
            self.logger.error(f"Element not found for select_by_text: by={by}, value={value}, text={text}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error selecting by text: by={by}, value={value}, text={text}, error={exc}")
            raise

    def select_by_value(self, by: str, value: str, option_value: str,
                         timeout: Optional[int] = None) -> None:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"select_by_value is not supported in context={self.driver.current_context}"
            )
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            Select(element).select_by_value(option_value)
        except TimeoutException:
            self.logger.error(f"Element not found for select_by_value: by={by}, value={value}, option_value={option_value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error selecting by value: by={by}, value={value}, option_value={option_value}, error={exc}")
            raise

    def get_select_options(self, by: str, value: str,
                            timeout: Optional[int] = None) -> List[str]:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"get_select_options is not supported in context={self.driver.current_context}"
            )
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return [option.text for option in Select(element).options]
        except TimeoutException:
            self.logger.error(f"Element not found for get_select_options: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting select options: by={by}, value={value}, error={exc}")
            raise

    def scroll_to_element(self, by: str, value: str, timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            if self.driver.current_context == "NATIVE_APP":
                if self.platform == "android":
                    self.driver.execute_script("mobile: scrollGesture", {
                        "elementId": element.id, "direction": "down", "percent": 1.0,
                    })
                else:
                    self.driver.execute_script("mobile: scroll", {
                        "elementId": element.id, "toVisible": True,
                    })
            else:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        except TimeoutException:
            self.logger.error(f"Element not found for scroll_to_element: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error scrolling to element: by={by}, value={value}, error={exc}")
            raise

    def scroll_to_bottom(self, max_swipes: int = 10) -> None:
        try:
            if self.driver.current_context == "NATIVE_APP":
                size = self.driver.get_window_size()
                for _ in range(max_swipes):
                    if self.platform == "android":
                        self.driver.execute_script("mobile: swipeGesture", {
                            "left": 0, "top": 0, "width": size["width"], "height": size["height"],
                            "direction": "up", "percent": 0.75,
                        })
                    else:
                        self.driver.execute_script("mobile: swipe", {"direction": "up"})
            else:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except WebDriverException as exc:
            self.logger.error(f"Driver error scrolling to bottom: max_swipes={max_swipes}, error={exc}")
            raise

    def scroll_to_top(self, max_swipes: int = 10) -> None:
        try:
            if self.driver.current_context == "NATIVE_APP":
                size = self.driver.get_window_size()
                for _ in range(max_swipes):
                    if self.platform == "android":
                        self.driver.execute_script("mobile: swipeGesture", {
                            "left": 0, "top": 0, "width": size["width"], "height": size["height"],
                            "direction": "down", "percent": 0.75,
                        })
                    else:
                        self.driver.execute_script("mobile: swipe", {"direction": "down"})
            else:
                self.driver.execute_script("window.scrollTo(0, 0);")
        except WebDriverException as exc:
            self.logger.error(f"Driver error scrolling to top: max_swipes={max_swipes}, error={exc}")
            raise

    def switch_to_frame(self, by: str, value: str, timeout: Optional[int] = None) -> None:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"switch_to_frame is not supported in context={self.driver.current_context}"
            )
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            WebDriverWait(self.driver, wait_time).until(
                EC.frame_to_be_available_and_switch_to_it((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Frame not available: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error switching to frame: by={by}, value={value}, error={exc}")
            raise

    def switch_to_default_content(self) -> None:
        if self.driver.current_context == "NATIVE_APP":
            raise NotImplementedError(
                f"switch_to_default_content is not supported in context={self.driver.current_context}"
            )
        try:
            self.driver.switch_to.default_content()
        except WebDriverException as exc:
            self.logger.error(f"Driver error switching to default content: error={exc}")
            raise

    def switch_to_context(self, context: str) -> None:
        try:
            self.driver.switch_to.context(context)
        except WebDriverException as exc:
            self.logger.error(f"Driver error switching to context: context={context}, error={exc}")
            raise

    def get_contexts(self) -> List[str]:
        try:
            return self.driver.contexts
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting contexts: error={exc}")
            raise

    def switch_to_webview(self, index: int = -1) -> str:
        try:
            webview_contexts = [c for c in self.driver.contexts if c.startswith("WEBVIEW_")]
            context_name = webview_contexts[index]
            self.driver.switch_to.context(context_name)
            return context_name
        except WebDriverException as exc:
            self.logger.error(f"Driver error switching to webview: index={index}, error={exc}")
            raise

    def tap(self, x: int, y: int) -> None:
        try:
            actions = ActionBuilder(self.driver, mouse=PointerInput(POINTER_TOUCH, "finger"))
            actions.pointer_action.move_to_location(x, y)
            actions.pointer_action.pointer_down()
            actions.pointer_action.pointer_up()
            actions.perform()
        except WebDriverException as exc:
            self.logger.error(f"Driver error tapping: x={x}, y={y}, error={exc}")
            raise

    def long_press(self, by: str, value: str, duration_ms: int = 1000,
                    timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            if self.platform == "android":
                self.driver.execute_script("mobile: longClickGesture", {
                    "elementId": element.id, "duration": duration_ms,
                })
            else:
                self.driver.execute_script("mobile: touchAndHold", {
                    "elementId": element.id, "duration": duration_ms / 1000,
                })
        except TimeoutException:
            self.logger.error(f"Element not found for long_press: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error long-pressing element: by={by}, value={value}, error={exc}")
            raise

    def swipe(self, direction: str, percent: float = 0.75, by: Optional[str] = None,
              value: Optional[str] = None, timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = None
            if by is not None and value is not None:
                element = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((by, value))
                )
            if self.platform == "android":
                if element is not None:
                    self.driver.execute_script("mobile: swipeGesture", {
                        "elementId": element.id, "direction": direction, "percent": percent,
                    })
                else:
                    size = self.driver.get_window_size()
                    self.driver.execute_script("mobile: swipeGesture", {
                        "left": 0, "top": 0, "width": size["width"], "height": size["height"],
                        "direction": direction, "percent": percent,
                    })
            else:
                if element is not None:
                    self.driver.execute_script("mobile: swipe", {
                        "elementId": element.id, "direction": direction,
                    })
                else:
                    self.driver.execute_script("mobile: swipe", {"direction": direction})
        except TimeoutException:
            self.logger.error(f"Element not found for swipe: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error swiping: direction={direction}, by={by}, value={value}, error={exc}")
            raise

    def scroll_until_visible(self, by: str, value: str, direction: str = "down",
                              max_swipes: int = 10) -> WebElement:
        try:
            size = self.driver.get_window_size()
            for _ in range(max_swipes):
                found = self.find_elements(by, value, timeout=1)
                if found:
                    return found[0]
                if self.platform == "android":
                    self.driver.execute_script("mobile: scrollGesture", {
                        "left": 0, "top": 0, "width": size["width"], "height": size["height"],
                        "direction": direction, "percent": 1.0,
                    })
                else:
                    self.driver.execute_script("mobile: scroll", {"direction": direction})
            return WebDriverWait(self.driver, self.explicit_wait).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Element not found for scroll_until_visible: by={by}, value={value}, direction={direction}, max_swipes={max_swipes}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error scrolling until visible: by={by}, value={value}, error={exc}")
            raise

    def drag_and_drop(self, by: str, value: str, end_x: int, end_y: int,
                       timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            if self.platform == "android":
                self.driver.execute_script("mobile: dragGesture", {
                    "elementId": element.id, "endX": end_x, "endY": end_y,
                })
            else:
                actions = ActionBuilder(self.driver, mouse=PointerInput(POINTER_TOUCH, "finger"))
                actions.pointer_action.move_to(element)
                actions.pointer_action.pointer_down()
                actions.pointer_action.move_to_location(end_x, end_y)
                actions.pointer_action.pointer_up()
                actions.perform()
        except TimeoutException:
            self.logger.error(f"Element not found for drag_and_drop: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error dragging element: by={by}, value={value}, end_x={end_x}, end_y={end_y}, error={exc}")
            raise

    def pinch_open(self, by: str, value: str, percent: float = 0.75,
                    timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            if self.platform == "android":
                self.driver.execute_script("mobile: pinchOpenGesture", {
                    "elementId": element.id, "percent": percent,
                })
            else:
                self.driver.execute_script("mobile: pinch", {
                    "elementId": element.id, "scale": 1 + percent, "velocity": 1.0,
                })
        except TimeoutException:
            self.logger.error(f"Element not found for pinch_open: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error pinch-opening element: by={by}, value={value}, error={exc}")
            raise

    def pinch_close(self, by: str, value: str, percent: float = 0.75,
                     timeout: Optional[int] = None) -> None:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            if self.platform == "android":
                self.driver.execute_script("mobile: pinchCloseGesture", {
                    "elementId": element.id, "percent": percent,
                })
            else:
                self.driver.execute_script("mobile: pinch", {
                    "elementId": element.id, "scale": max(1 - percent, 0.1), "velocity": 1.0,
                })
        except TimeoutException:
            self.logger.error(f"Element not found for pinch_close: by={by}, value={value}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error pinch-closing element: by={by}, value={value}, error={exc}")
            raise

    def get_current_context(self) -> str:
        try:
            return self.driver.current_context
        except WebDriverException as exc:
            self.logger.error(f"Driver error getting current context: error={exc}")
            raise

    def switch_to_native(self) -> None:
        try:
            self.driver.switch_to.context("NATIVE_APP")
        except WebDriverException as exc:
            self.logger.error(f"Driver error switching to native context: error={exc}")
            raise

    def wait_for_context(self, pattern: str = "WEBVIEW", timeout: Optional[int] = None) -> str:
        wait_time = timeout if timeout is not None else self.explicit_wait
        try:
            return WebDriverWait(self.driver, wait_time).until(
                lambda d: next((c for c in d.contexts if pattern in c), None)
            )
        except TimeoutException:
            self.logger.error(f"No context matched pattern: pattern={pattern}, timeout={wait_time}")
            raise
        except WebDriverException as exc:
            self.logger.error(f"Driver error waiting for context: pattern={pattern}, error={exc}")
            raise

    def activate_app(self, app_id: str) -> None:
        try:
            self.driver.activate_app(app_id)
        except WebDriverException as exc:
            self.logger.error(f"Driver error activating app: app_id={app_id}, error={exc}")
            raise

    def terminate_app(self, app_id: str) -> bool:
        try:
            return self.driver.terminate_app(app_id)
        except WebDriverException as exc:
            self.logger.error(f"Driver error terminating app: app_id={app_id}, error={exc}")
            raise

    def install_app(self, app_path: str) -> None:
        try:
            self.driver.install_app(app_path)
        except WebDriverException as exc:
            self.logger.error(f"Driver error installing app: app_path={app_path}, error={exc}")
            raise

    def remove_app(self, app_id: str) -> bool:
        try:
            return self.driver.remove_app(app_id)
        except WebDriverException as exc:
            self.logger.error(f"Driver error removing app: app_id={app_id}, error={exc}")
            raise

    def query_app_state(self, app_id: str) -> int:
        try:
            return self.driver.query_app_state(app_id)
        except WebDriverException as exc:
            self.logger.error(f"Driver error querying app state: app_id={app_id}, error={exc}")
            raise
