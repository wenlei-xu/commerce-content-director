# Workflow: script production

读取一条已锁定创意方向，以及产品硬事实、主体和当前配置。生成本地 structured_script，先运行校验器，再渲染全部审核字段；只有校验通过才创建或更新待审核脚本。

审核意见只修改 structured_script。修订后重新校验和渲染。只有检查通过、审核意见处理完毕的脚本才能锁定。
