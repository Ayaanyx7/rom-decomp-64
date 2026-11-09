from .gbi1 import GBI1
import vertices
from utils import debug_print


class GBI0(GBI1):
    def __init__(self):
        super().__init__()
        self.vertex_stride = 10
        # GBI0 overrides
        self.commands.update(
            {
                0x01: self.execute_sp_matrix,
                0x03: self.execute_move_mem,
                0x04: self.execute_vertex,
                0x05: self.execute_reserved,
                0x07: self.execute_reserved,
                0x0B: self.execute_pop_matrix,
                0x0F: self.execute_rdp_half_cont,
                0x15: self.execute_set_other_mode_l,
                0x16: self.execute_set_geometry_mode,
                0x17: self.execute_clear_geometry_mode,
                0x18: self.execute_end_dl,
                0x1D: self.execute_move_word,
                0x1E: self.execute_move_mem,
                0xB0: self.execute_unknown,
                0xB1: self.execute_tri4,
                0xB2: self.execute_rdp_half_cont,
                0xBE: self.execute_cull_dl,
                
                # Missing Texture & Pixel Blending Pipeline (F3D Hardware Standards)
                0x20: self.execute_dp_set_texture_image,
                0x21: self.execute_dp_set_depth_image,
                0x22: self.execute_dp_set_color_image,
                0x24: self.execute_dp_set_blend_color,
                0x25: self.execute_dp_set_fog_color,
                0x26: self.execute_dp_set_prim_color,
                0x27: self.execute_dp_set_env_color,
                0x28: self.execute_dp_set_combine_mode,
                0x29: self.execute_dp_set_tile,
                0x2A: self.execute_dp_load_tile,
                0x2B: self.execute_dp_load_block,
                0x2C: self.execute_dp_set_tile_size,
                0x2D: self.execute_dp_load_tlut,
                0x2E: self.execute_dp_set_scissor,
                0x2F: self.execute_dp_set_prim_depth,
                0x30: self.execute_dp_set_other_mode,
                0x36: self.execute_dp_fill_rectangle,
                0x37: self.execute_dp_set_fill_color,
                0x3F: self.execute_set_other_mode_h,
            }
        )

    def execute_cull_dl(self, cmd0, cmd1, dis):
        # GBI0 uses 24 bits for start index
        vstart = (cmd0 & 0x00FFFFFF) // 40
        vend = cmd1 // 40

        if dis:
            dis.set_cmd("gsSPCullDisplayList", {"v0": vstart, "vn": vend})

    def execute_vertex(self, cmd0, cmd1, dis):
        n = self._SHIFTR(cmd0, 20, 4) + 1
        v0 = self._SHIFTR(cmd0, 16, 4)
        address = cmd1

        if dis:
            vertices_record = vertices.parse_vertices(
                address, n, dis.sTxt, dis.context_prefix, self.parent_dl
            )
            if vertices_record is None:
                debug_print(f"Failed to parse vertices at address {address}")
                return
            dis.set_cmd(
                "gsSPVertex",
                {
                    "vertices": vertices_record,
                    "count": n,
                    "v0": v0,
                },
            )

    def execute_tri4(self, cmd0, cmd1, dis):
        idx09 = self._SHIFTR(cmd0, 12, 4)
        idx06 = self._SHIFTR(cmd0, 8, 4)
        idx03 = self._SHIFTR(cmd0, 4, 4)
        idx00 = self._SHIFTR(cmd0, 0, 4)

        idx11 = self._SHIFTR(cmd1, 28, 4)
        idx10 = self._SHIFTR(cmd1, 24, 4)
        idx08 = self._SHIFTR(cmd1, 20, 4)
        idx07 = self._SHIFTR(cmd1, 16, 4)
        idx05 = self._SHIFTR(cmd1, 12, 4)
        idx04 = self._SHIFTR(cmd1, 8, 4)
        idx02 = self._SHIFTR(cmd1, 4, 4)
        idx01 = self._SHIFTR(cmd1, 0, 4)

        if dis:
            from texture import commit_textures

            commit_textures(dis.sTxt, dis.current_pos, [0, 1])
            dis.side_effects.append(
                {"type": "commit_textures", "pos": dis.current_pos, "tiles": [0, 1]}
            )

            indices_list = []

            if idx00 != idx01:
                indices_list.append([idx00, idx01, idx02])
            if idx03 != idx04:
                indices_list.append([idx03, idx04, idx05])
            if idx06 != idx07:
                indices_list.append([idx06, idx07, idx08])
            if idx09 != idx10:
                indices_list.append([idx09, idx10, idx11])

            dis.set_cmd("gsSP4Triangles", {"tris": indices_list})

    def execute_rdp_half_cont(self, cmd0, cmd1, dis):
        vtx = self._SHIFTR(cmd0, 16, 8)
        where = self._SHIFTR(cmd0, 12, 4)
        if dis:
            dis.set_cmd(
                "gsSPModifyVertex", {"vtx": vtx, "where": where, "val": cmd1}, commented_out=True
            )


class F3DEX_GBI0(GBI1):
    def __init__(self):
        super().__init__()
        self.vertex_stride = 10
        # Override vertex with GBI0 style
        self.commands[0x04] = self.execute_vertex

    def execute_vertex(self, cmd0, cmd1, dis):
        # GBI0 style vertex
        n = self._SHIFTR(cmd0, 20, 4) + 1
        v0 = self._SHIFTR(cmd0, 16, 4)
        address = cmd1

        if dis:
            vertices_record = vertices.parse_vertices(
                address, n, dis.sTxt, dis.context_prefix, self.parent_dl
            )
            if vertices_record is None:
                debug_print(f"Failed to parse vertices at address {address}")
                return
            dis.set_cmd(
                "gsSPVertex",
                {
                    "vertices": vertices_record,
                    "count": n,
                    "v0": v0,
                },
            )
