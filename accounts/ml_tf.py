HAS_TF = False

try:
    import tensorflow as tf  # type: ignore
    from tensorflow.keras.layers import TextVectorization  # type: ignore
    HAS_TF = True
except Exception:
    tf = None
    TextVectorization = None
    HAS_TF = False


def _vectorize_pair(text_a: str, text_b: str):
    """Builds a tiny on-the-fly vocabulary and vectorizes two texts.
    Returns float tensors of shape (vocab_size,) as term-frequency vectors.
    """
    if not HAS_TF:
        return None, None
    dataset = tf.data.Dataset.from_tensor_slices([text_a or '', text_b or ''])
    vec = TextVectorization(output_mode='count')
    vec.adapt(dataset.batch(2))
    a = vec([text_a or ''])
    b = vec([text_b or ''])
    return tf.cast(a[0], tf.float32), tf.cast(b[0], tf.float32)


def _cosine_sim_tf(a, b):
    if a is None or b is None:
        return 0.0
    a_norm = tf.norm(a)
    b_norm = tf.norm(b)
    denom = a_norm * b_norm
    if tf.equal(denom, 0.0):
        return 0.0
    sim = tf.tensordot(a, b, axes=1) / denom
    return float(sim.numpy())


def score_job_match_tf(resume_text: str, job_text: str) -> int:
    """Vectorize texts using Keras TextVectorization and compute cosine similarity.
    Maps to 0-100.
    """
    if not HAS_TF:
        return 0
    a, b = _vectorize_pair(resume_text, job_text)
    sim = _cosine_sim_tf(a, b)
    score = int(max(0, min(100, round(sim * 140))))
    return score


