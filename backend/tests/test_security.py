"""app.core.security 单元测试 —— 密码哈希 + JWT 签发/解码。

覆盖范围
--------
TestPasswordHash（6 条）
    - hash_password 输出格式：salt$digest，salt=32hex / digest=64hex
    - verify_password 正确 / 错误 / 空字符串 / 格式非法 / 加盐后仍可验证
TestJWT（5 条）
    - create_access_token / decode_token 往返
    - 过期 token 解码抛异常
    - 伪造 token 字符串解码抛异常
    - 密钥不匹配解码抛异常
    - 多用户 token 互不干扰

被测函数来自 app/core/security.py，无任何外部依赖，不需要网络、不需要模型。
"""
import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHash:
    """密码哈希：PBKDF2-SHA256 + 16字节随机盐，存储格式 salt$digest。"""

    def test_hash_format(self):
        """hash_password 输出必须是 '32位hex$64位hex' 两段。"""
        stored = hash_password("hello")
        assert stored.count("$") == 1
        salt, digest = stored.split("$")
        assert len(salt) == 32  # 16 bytes -> 32 hex
        assert len(digest) == 64  # sha256 -> 64 hex

    def test_verify_correct(self):
        """正确密码应返回 True。"""
        stored = hash_password("correct_password")
        assert verify_password("correct_password", stored) is True

    def test_verify_wrong(self):
        """错误密码应返回 False。"""
        stored = hash_password("correct_password")
        assert verify_password("wrong_password", stored) is False

    def test_verify_empty_stored(self):
        """空字符串密码哈希应安全返回 False，而不是抛异常。"""
        assert verify_password("anything", "") is False

    def test_verify_bad_format(self):
        """格式非法的哈希（没有 $）应返回 False。"""
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_hash_deterministic_for_same_input(self):
        """同一密码 hash 两次得到不同结果（不同盐），但 verify 都能过。"""
        pwd = "same-password-123"
        a = hash_password(pwd)
        b = hash_password(pwd)
        assert a != b  # 不同 salt，hash 值不一样
        assert verify_password(pwd, a) is True
        assert verify_password(pwd, b) is True


class TestJWT:
    """JWT：HS256 算法，payload 包含 sub=username + exp=过期时间。"""

    def test_round_trip(self):
        """签发后解码应能拿回原始 username。"""
        token = create_access_token("alice")
        assert decode_token(token) == "alice"

    def test_decode_expired_raises(self):
        """已过期的 token 解码应抛 PyJWTError。"""
        import datetime
        import jwt

        from app.core.config import settings

        payload = {
            "sub": "expired_user",
            "exp": datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(seconds=1),
        }
        expired = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        with pytest.raises(Exception):
            decode_token(expired)

    def test_decode_invalid_token_raises(self):
        """非 JWT 字符串解码应抛异常。"""
        with pytest.raises(Exception):
            decode_token("this-is-not-a-jwt")

    def test_decode_wrong_secret_raises(self):
        """用错误密钥签发的 token 解码应抛异常（签名校验失败）。"""
        import datetime
        import jwt

        payload = {
            "sub": "hacker",
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=1),
        }
        fake = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        with pytest.raises(Exception):
            decode_token(fake)

    def test_token_different_users(self):
        """不同 username 的 token 各自独立。"""
        t1 = create_access_token("user_a")
        t2 = create_access_token("user_b")
        assert decode_token(t1) == "user_a"
        assert decode_token(t2) == "user_b"
