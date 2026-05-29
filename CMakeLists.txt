cmake_minimum_required(VERSION 3.20)
project(tiny-ragemp-launcher CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

include(FetchContent)
FetchContent_Declare(
    imgui
    GIT_REPOSITORY https://github.com/ocornut/imgui.git
    GIT_TAG        v1.91.5
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(imgui)

set(IMGUI_SRC
    ${imgui_SOURCE_DIR}/imgui.cpp
    ${imgui_SOURCE_DIR}/imgui_draw.cpp
    ${imgui_SOURCE_DIR}/imgui_tables.cpp
    ${imgui_SOURCE_DIR}/imgui_widgets.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_win32.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_dx11.cpp
)

add_executable(tiny-ragemp-launcher WIN32
    src/main.cpp
    ${IMGUI_SRC}
)

target_include_directories(tiny-ragemp-launcher PRIVATE
    ${imgui_SOURCE_DIR}
    ${imgui_SOURCE_DIR}/backends
)

target_link_libraries(tiny-ragemp-launcher PRIVATE
    d3d11
    dxgi
    dwmapi
    advapi32
    shell32
    user32
)

target_compile_definitions(tiny-ragemp-launcher PRIVATE
    UNICODE _UNICODE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
)

if (MSVC)
    target_compile_options(tiny-ragemp-launcher PRIVATE /W3 /permissive- /utf-8)
endif()
