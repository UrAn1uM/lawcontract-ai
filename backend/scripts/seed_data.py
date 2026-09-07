"""初始化知识库种子数据：标准条款库 + 法规库。

用法（在 backend 目录下）：
    python -m scripts.seed_data

注意：种子法规条文为教学示范的节选/改写，生产使用请以官方公布文本为准。
之后需要执行 python -m scripts.rebuild_index 构建向量索引。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402

CLAUSES = [
    {
        "title": "违约责任条款（标准对等）",
        "category": "违约责任",
        "risk_level": "高",
        "content": "任何一方违反本合同约定的，应向守约方支付合同总价款百分之二十的违约金；违约金不足以弥补守约方实际损失的，违约方还应就差额部分承担赔偿责任。双方违约责任对等适用。",
        "source": "标准条款模板",
    },
    {
        "title": "付款条款（标准）",
        "category": "付款",
        "risk_level": "中",
        "content": "甲方应于本合同签订后七个工作日内支付合同总价款百分之三十作为预付款；乙方交付全部成果且甲方验收合格后十个工作日内，甲方支付剩余百分之七十价款。付款方式为银行转账至乙方指定账户。",
        "source": "标准条款模板",
    },
    {
        "title": "保密条款（双向对等）",
        "category": "保密",
        "risk_level": "中",
        "content": "双方对在签订和履行本合同过程中知悉的对方商业秘密、技术秘密及经营信息负有保密义务，未经对方书面同意不得向任何第三方披露或用于本合同以外的目的。保密期限为本合同有效期内及合同终止后三年。",
        "source": "标准条款模板",
    },
    {
        "title": "知识产权归属条款",
        "category": "知识产权",
        "risk_level": "高",
        "content": "本合同履行过程中产生的工作成果，其知识产权归属由双方书面约定；未约定的，归实际创作方所有。一方提供的背景知识产权仍归该方所有，另一方仅在履行本合同必需的范围内使用。",
        "source": "标准条款模板",
    },
    {
        "title": "验收条款（标准）",
        "category": "验收",
        "risk_level": "中",
        "content": "乙方交付成果后，甲方应在收到之日起十个工作日内完成验收并出具书面验收意见；逾期未提出异议的视为验收合格。验收不合格的，乙方应在甲方指定期限内无偿修改直至合格。",
        "source": "标准条款模板",
    },
    {
        "title": "争议解决条款（标准）",
        "category": "争议解决",
        "risk_level": "低",
        "content": "因本合同引起的或与本合同有关的任何争议，双方应首先友好协商解决；协商不成的，任何一方均有权向合同签订地有管辖权的人民法院提起诉讼。",
        "source": "标准条款模板",
    },
    {
        "title": "不可抗力条款（标准）",
        "category": "不可抗力",
        "risk_level": "低",
        "content": "因不可抗力不能履行合同的，根据不可抗力的影响，部分或全部免除责任，但应及时通知对方并在合理期限内提供证明。不可抗力指不能预见、不能避免且不能克服的客观情况。",
        "source": "标准条款模板",
    },
    {
        "title": "数据处理与个人信息保护条款",
        "category": "数据合规",
        "risk_level": "高",
        "content": "乙方为履行本合同处理甲方个人信息或业务数据的，应遵循合法、正当、必要和最小化原则，仅限于合同约定目的和范围内处理，并采取加密、访问控制等必要安全措施；未经甲方书面同意不得转委托或向境外提供。发生数据安全事件的，乙方应立即通知甲方并采取补救措施。",
        "source": "标准条款模板",
    },
    {
        "title": "通知送达条款",
        "category": "通知送达",
        "risk_level": "低",
        "content": "双方确认以本合同首部载明的地址、电子邮箱为有效送达地址。一方变更送达地址应提前书面通知对方，否则按原地址送达即视为有效送达。",
        "source": "标准条款模板",
    },
    {
        "title": "合同解除条款（对等）",
        "category": "解除终止",
        "risk_level": "中",
        "content": "一方严重违约致使合同目的不能实现的，另一方有权书面通知解除本合同。任何一方均可与对方协商一致解除本合同。合同解除不影响违约责任及争议解决条款的效力。",
        "source": "标准条款模板",
    },
]

REGULATIONS = [
    {
        "name": "数据安全法",
        "article_no": "第二十一条",
        "jurisdiction": "中国",
        "effective_date": "2021-09-01",
        "content": "国家建立数据分类分级保护制度，根据数据在经济社会发展中的重要程度，以及一旦遭到篡改、破坏、泄露或者非法获取、非法利用，对国家安全、公共利益或者个人、组织合法权益造成的危害程度，对数据实行分类分级保护。",
    },
    {
        "name": "数据安全法",
        "article_no": "第二十七条",
        "jurisdiction": "中国",
        "effective_date": "2021-09-01",
        "content": "开展数据处理活动应当依照法律、法规的规定，建立健全全流程数据安全管理制度，组织开展数据安全教育培训，采取相应的技术措施和其他必要措施，保障数据安全。",
    },
    {
        "name": "数据安全法",
        "article_no": "第三十条",
        "jurisdiction": "中国",
        "effective_date": "2021-09-01",
        "content": "重要数据的处理者应当按照规定对其数据处理活动定期开展风险评估，并向有关主管部门报送风险评估报告。风险评估报告应当包括处理的重要数据的种类、数量，开展数据处理活动的情况，面临的数据安全风险及其应对措施等。",
    },
    {
        "name": "个人信息保护法",
        "article_no": "第十三条",
        "jurisdiction": "中国",
        "effective_date": "2021-11-01",
        "content": "符合下列情形之一的，个人信息处理者方可处理个人信息：（一）取得个人的同意；（二）为订立、履行个人作为一方当事人的合同所必需，或者按照依法制定的劳动规章制度和依法签订的集体合同实施人力资源管理所必需；（三）为履行法定职责或者法定义务所必需；（四）为应对突发公共卫生事件等紧急情况所必需；（五）为公共利益实施新闻报道、舆论监督等行为在合理的范围内处理个人信息；（六）依照本法规定在合理的范围内处理个人自行公开或者其他已经合法公开的个人信息；（七）法律、行政法规规定的其他情形。",
    },
    {
        "name": "个人信息保护法",
        "article_no": "第十七条",
        "jurisdiction": "中国",
        "effective_date": "2021-11-01",
        "content": "个人信息处理者在处理个人信息前，应当以显著方式、清晰易懂的语言真实、准确、完整地将个人信息处理者的名称和联系方式、处理目的、处理方式、处理的个人信息种类、保存期限等事项告知个人。",
    },
    {
        "name": "个人信息保护法",
        "article_no": "第五十一条",
        "jurisdiction": "中国",
        "effective_date": "2021-11-01",
        "content": "个人信息处理者应当根据个人信息的处理目的、处理方式、个人信息的种类以及对个人权益的影响、可能存在的安全风险等，采取下列措施确保个人信息处理活动符合法律、行政法规的规定：制定内部管理制度和操作规程；对个人信息实行分类管理；采取相应的加密、去标识化等安全技术措施；合理确定个人信息处理的操作权限，并定期对从业人员进行安全教育和培训；制定并组织实施个人信息安全事件应急预案。",
    },
    {
        "name": "个人信息保护法",
        "article_no": "第三十八条",
        "jurisdiction": "中国",
        "effective_date": "2021-11-01",
        "content": "个人信息处理者因业务等需要，确需向中华人民共和国境外提供个人信息的，应当具备下列条件之一：（一）通过国家网信部门组织的安全评估；（二）按照国家网信部门的规定经专业机构进行个人信息保护认证；（三）按照国家网信部门制定的标准合同与境外接收方订立合同，约定双方的权利和义务；（四）法律、行政法规或者国家网信部门规定的其他条件。",
    },
    {
        "name": "GDPR",
        "article_no": "第5条",
        "jurisdiction": "欧盟",
        "effective_date": "2018-05-25",
        "content": "个人数据应当以合法、公平、透明的方式处理；收集应具有特定、明确、合法的目的，不得以与该目的相悖的方式进一步处理；处理应限于实现处理目的所必需的最小范围；数据应当准确且保持最新；存储期限不得长于实现目的所必需的时间；处理过程中应确保数据完整性与保密性。",
    },
    {
        "name": "GDPR",
        "article_no": "第6条",
        "jurisdiction": "欧盟",
        "effective_date": "2018-05-25",
        "content": "只有在符合以下至少一项条件时，处理才被视为合法：（a）数据主体已同意；（b）处理是为履行数据主体为一方当事人的合同所必需；（c）处理是为履行控制者法定义务所必需；（d）处理是为保护数据主体或他人的重大利益所必需；（e）处理是为公共利益或公权力行使所必需；（f）处理是为控制者或第三方追求的合法利益所必需，且不损害数据主体的权利与自由。",
    },
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 默认管理员账号 admin / admin123
        if db.query(models.User).filter(models.User.username == "admin").first():
            print("管理员账号已存在，跳过创建")
        else:
            db.add(models.User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
            ))
            print("已创建管理员账号 admin / admin123")

        # 默认普通用户 demo / demo123
        if db.query(models.User).filter(models.User.username == "demo").first():
            print("普通用户 demo 已存在，跳过创建")
        else:
            db.add(models.User(
                username="demo",
                password_hash=hash_password("demo123"),
                role="user",
            ))
            print("已创建普通用户 demo / demo123")

        if db.query(models.Clause).count() > 0:
            print("条款库已有数据，跳过种子导入（如需重新导入请先清空 clauses 表）")
        else:
            for c in CLAUSES:
                db.add(models.Clause(**c))
            print(f"已导入 {len(CLAUSES)} 条标准条款")

        if db.query(models.Regulation).count() > 0:
            print("法规库已有数据，跳过种子导入（如需重新导入请先清空 regulations 表）")
        else:
            for r in REGULATIONS:
                db.add(models.Regulation(**r))
            print(f"已导入 {len(REGULATIONS)} 条法规条文")

        db.commit()
        print("完成。下一步：python -m scripts.rebuild_index 构建向量索引")
    finally:
        db.close()


if __name__ == "__main__":
    main()
