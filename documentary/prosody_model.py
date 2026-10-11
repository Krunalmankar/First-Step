"""Add prosody controls to the Kokoro-82M ONNX graph (one-time model surgery).

Kokoro (StyleTTS2 family) predicts, per sentence: a duration for every phoneme token, a pitch
contour F0 (Hz, two values per frame) and an energy contour N. The vocoder then renders audio
from them. This script inserts three controls at exactly those points and exposes the
predictions, so narration can be shaped like a human read — emphasis, rises and falls, pauses —
while the neural vocoder still synthesises every sample (no post-processing pitch shifting):

  inputs  dur_scale [1, S]   multiplies each token's duration      (1 = unchanged)
          f0_mul    [1, F]   multiplies the pitch contour per frame (1 = unchanged; broadcastable)
          n_add     [1, F]   offsets the energy contour per frame   (0 = unchanged; broadcastable)
  outputs durations [1, S]   frames per token, as used
          f0_pred   [1, F]   predicted pitch contour, before f0_mul
          n_pred    [1, F]   predicted energy contour, before n_add

    python3 prosody_model.py   (reads build/models/kokoro-v1.0.onnx, writes kokoro-v1.0-prosody.onnx)
"""
from pathlib import Path

import onnx
from onnx import TensorProto, helper

HERE = Path(__file__).parent
MODELS = HERE / "build" / "models"
SRC, DST = MODELS / "kokoro-v1.0.onnx", MODELS / "kokoro-v1.0-prosody.onnx"

DUR_IN, DUR_OUT = "/encoder/Div_output_0", "/encoder/Clip_output_0"     # seconds-free token durations
F0_T, N_T = "/encoder/Reshape_output_0", "/encoder/Reshape_1_output_0"  # contours fed to the decoder


def rewire(graph, old, new, skip):
    for node in graph.node:
        if node is skip:
            continue
        for k, name in enumerate(node.input):
            if name == old:
                node.input[k] = new


def build():
    m = onnx.load(str(SRC))
    g = m.graph
    names = {o for n in g.node for o in n.output}
    for t in (DUR_IN, DUR_OUT, F0_T, N_T):
        assert t in names, f"tensor {t} not found: this script expects the kokoro-onnx v1.0 export"

    g.input.extend([
        helper.make_tensor_value_info("dur_scale", TensorProto.FLOAT, [1, "sequence_length"]),
        helper.make_tensor_value_info("f0_mul", TensorProto.FLOAT, [1, "f0_frames"]),
        helper.make_tensor_value_info("n_add", TensorProto.FLOAT, [1, "n_frames"]),
    ])
    mul_d = helper.make_node("Mul", [DUR_IN, "dur_scale"], ["prosody/dur_scaled"], name="prosody/dur_mul")
    mul_f = helper.make_node("Mul", [F0_T, "f0_mul"], ["prosody/f0_out"], name="prosody/f0_mul")
    add_n = helper.make_node("Add", [N_T, "n_add"], ["prosody/n_out"], name="prosody/n_add")
    for node, old, new in ((mul_d, DUR_IN, "prosody/dur_scaled"), (mul_f, F0_T, "prosody/f0_out"),
                           (add_n, N_T, "prosody/n_out")):
        rewire(g, old, new, skip=node)
    # keep the graph topologically sorted: insert each new node right after its producer
    nodes = list(g.node)
    for new in (mul_d, mul_f, add_n):
        src = new.input[0]
        idx = next(i for i, n in enumerate(nodes) if src in n.output)
        nodes.insert(idx + 1, new)
    del g.node[:]
    g.node.extend(nodes)
    # expose predictions (identity copies so output names are stable)
    for src, out in ((DUR_OUT, "durations"), (F0_T, "f0_pred"), (N_T, "n_pred")):
        g.node.append(helper.make_node("Identity", [src], [out], name=f"prosody/{out}"))
    g.output.extend([
        helper.make_tensor_value_info("durations", TensorProto.FLOAT, [1, "sequence_length"]),
        helper.make_tensor_value_info("f0_pred", TensorProto.FLOAT, [1, "f0_frames"]),
        helper.make_tensor_value_info("n_pred", TensorProto.FLOAT, [1, "n_frames"]),
    ])
    onnx.save(m, str(DST))
    print("wrote", DST)


if __name__ == "__main__":
    build()
