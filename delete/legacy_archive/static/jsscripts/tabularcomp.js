/** TABULAR TREATMENT COMPONENTs **/
/** written by J.CHOU@ate-lab 2023-04-20**/
function setDefault(val, val_default){
	if (val === null || val === undefined){
		return val_default;
	} else {
		return val;
	}
}

function importFile(vm, url, colConfig, innerFunc){
	const input = document.createElement('input');
	input.type = 'file';
	input.accept = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
	input.onchange = () => {
		const file = input.files[0];
		if (file) {
			let loading = vm.$loading({
				lock: true,
				text: '加载中，请稍候...',
				spinner: 'el-icon-loading',
				background: 'rgba(0, 10, 0, 0.5)'
			})

			let formData = new FormData()
			formData.append("tableDataFile", file)
			formData.append("colConfig", JSON.stringify(colConfig))

			axios.post(url, formData).then(response => {
				innerFunc(vm, response.data);
				loading.close();
			}).catch(error => {
				vm.$message.error("文件解析失败");
				loading.close();
			})
		} else {
			vm.$message.error("未上传配置文件")
		}
	}
	input.click();
}

function downloadFile(vm, url, colConfig, tableData, defaultFilename){
	let loading = vm.$loading({
		lock: true,
		text: '加载中，请稍候...',
		spinner: 'el-icon-loading',
		background: 'rgba(0, 10, 0, 0.5)'
	});
	var formData = new FormData();
	formData.append("colConfig", JSON.stringify(colConfig))
	formData.append("tableData", JSON.stringify(tableData))
	formData.append("filename", defaultFilename)

	// P.S. while send blob-stream file, add option `{responseType:'blob'}`
	//         to cancel default response-decode process
	axios.post(url, formData, {responseType:'blob'}).then(response => {
		let fileBlob = new Blob(
			[response.data],
			{ type: response.headers["content-type"] },
		);
		const link = document.createElement('a');
		let filename = decodeURI(response.headers["content-disposition"]).split("filename");
		filename = filename[filename.length-1].split("=")[1].split('\'');
		link.download = setDefault(defaultFilename, filename[filename.length-1].split(";")[0]);
		link.href = window.URL.createObjectURL(fileBlob);
		link.click();
		window.URL.revokeObjectURL(link.href);
		loading.close();
	}).catch(error => {
		vm.$message.error("文件下载失败");
		loading.close();
	})
}

new function(){
	Vue.component("ate-tabular-base", {
    props: [
      "table-data",
      "col-config",
      "data-load",
      "max-height",
      "page-size",
      "global-operatable",
      "local-operatable",
      "checkable",
      "check-url",
      "importable",
      "import-url",
      "exportable",
      "export-url",
      "export-filename",
    ],
    template: `
			<div style="display: flex; flex-direction: column; align-items: center; width: 100%; height: 100%;">
					<div
						v-if="setDefault(globalOperatable, true)"
						style="display: flex; width: calc(100% - 2rem); flex-direction: row; justify-content: space-between; padding: 0.5rem 0;"
					>
						<el-button-group v-if="setDefault(importable, true)||setDefault(exportable, true)">
							<el-button type="success" plain size="mini" @click="importData" v-if="setDefault(importable, true)">导入条目</el-button>
							<el-button type="warning" plain size="mini" @click="exportData" v-if="setDefault(exportable, true)">导出条目</el-button>
						</el-button-group>
						<el-button-group>
							<el-button type="primary" plain size="mini" @click="checkAll" :disabled="checkPass" v-if="setDefault(checkable, false)">检查条目</el-button>
							<el-button type="success" plain size="mini" @click="addLine(currentPage*setDefault(pageSize, 10)-2)">添加条目</el-button>
							<el-button type="warning" plain size="mini" @click="delPage">删除本页</el-button>
							<el-button type="danger" plain size="mini" @click="clearAll">清空条目</el-button>
						</el-button-group>
					</div>
					<el-form
						:inline="true"
						:model="searchBox"
						label-width="100px"
						size="mini"
						label-position="top"
						style="display: flex; justify-content: space-around; align-items: center; width: 100%;"
					>
						<el-form-item
							v-for="itm of colConfig"
							v-if="setDefault(itm.searchable, true)"
							:label="itm.name"
							:key="itm.key"
						>
							<el-input-number
								v-model="searchBox[itm.key]"
								:max="itm.max"
								:min="itm.min"
								:step="itm.step"
								:step-strictly="itm.stepstrictly"
								:placeholder="'请输入待查询的'+itm.name"
								clearable
								@input="e=>changeValue()"
								v-if="itm.inputType == 'input-number'"
							/>
							<el-input
								v-model="searchBox[itm.key]"
								:placeholder="'请输入待查询的'+itm.name"
								clearable
								@input="e=>changeValue()"
								v-else-if="setDefault(itm.inputType, 'input') == 'input'"
							/>
							<el-select
								v-model="searchBox[itm.key]"
								:multiple="itm.multiple"
								filterable
								:clearable="itm.multiple"
								:placeholder="'请输入待查询的'+itm.name"
								@change="e=>changeValue()"
								v-if="itm.inputType == 'select'"
							>
								<el-option label="显示全部" value="all" v-if="!itm.multiple" />
								<el-option
									v-for="label, key in itm.options"
									:key="key"
									:label="label"
									:value="key"
								/>
							</el-select>
							<el-select
								v-model="searchBox[itm.key]"
								:multiple="itm.multiple"
								filterable
								:placeholder="'请输入待查询的'+itm.name"
								@change="e=>changeValue()"
								v-if="itm.inputType == 'switch'">
								<el-option label="显示全部" value="all"></el-option>
								<el-option :label="setDefault(itm.trueLabel, '显示勾选项')" :value="true" />
								<el-option :label="setDefault(itm.falseLabel, '显示未勾选项')" :value="false" />
							</el-select>
						</el-form-item>
						<el-form-item>
							<el-button type="primary" size="mini" @click="filterSearch">筛选</el-button>
						</el-form-item>
					</el-form>
        	<el-table
						:data="dataShowInfo.slice((currentPage-1)*setDefault(pageSize, 10),currentPage*setDefault(pageSize, 10))"
						size="small"
						:max-height="setDefault(maxHeight, 500)"
					>
						<el-table-column label="序号" :show-overflow-tooltip="true" :width="120">
							<template slot-scope="scope">
								<span>{{ showId[(currentPage-1)*setDefault(pageSize, 10)+scope.$index]+1 }}</span>
							</template>
						</el-table-column>
						<el-table-column :label="itm.name" :show-overflow-tooltip="true"
							v-for="itm of colConfig" :key="itm.key" v-if="itm.key !== '_tabular_comp_private_log'">
							<template slot-scope="scope">
								<el-switch v-model="scope.row[itm.key]" size="mini"
									:active-color="setDefault(itm.activeColor, '#13ce66')"
									:inactive-color="setDefault(itm.activeColor, '#ff4949')"
									v-if="itm.inputType == 'switch'"
									@change="e=>editValue((currentPage-1)*setDefault(pageSize, 10)+scope.$index, itm.key)">
								</el-switch>
								<div v-else-if="setDefault(scope.row.editable,true)">
									<el-input type="number" v-model="scope.row[itm.key]" size="mini" :placeholder="itm.placeholder"
										:max="itm.max" :min="itm.min" :step="itm.step" :step-strictly="itm.stepstrictly"
										v-if="itm.inputType == 'input-number'"
										@blur="e=>editValue((currentPage-1)*setDefault(pageSize, 10)+scope.$index, itm.key)"></el-input>
									<el-input v-model="scope.row[itm.key]" size="mini" :placeholder="itm.placeholder"
										v-else-if="setDefault(itm.inputType, 'input') == 'input'"
										@blur="e=>editValue((currentPage-1)*setDefault(pageSize, 10)+scope.$index, itm.key)"></el-input>
									<el-select v-model="scope.row[itm.key]" size="mini" :placeholder="itm.placeholder"
										:multiple="itm.multiple" filterable
										v-else-if="itm.inputType == 'select'"
										@change="e=>editValue((currentPage-1)*setDefault(pageSize, 10)+scope.$index, itm.key)">
										<el-option v-for="label, key in itm.options" :key="key"
												:label="label" :value="key">
										</el-option>
									</el-select>
								</div>
								<div v-else-if="itm.inputType == 'select'">
									<div v-if="itm.outputType=='tag' && itm.multiple">
										<div v-for="it of scope.row[itm.key].slice(0, setDefault(itm.outputTagMax, 5))"  :key="it">
											<span v-if="!it"></span>
											<el-popover placement="right" trigger="hover"
												v-else-if="setDefault(itm.options[it], it).length>setDefault(itm.outputTextMax, 30)">
												<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
															white-space: pre-line; word-break: break-all; word-wrap: break-word;">
													{{ setDefault(itm.options[it], it) }}
												</span>
												<el-tag size="mini" type="primary" slot="reference">
													{{ setDefault(itm.options[it], it).slice(0, setDefault(itm.outputTextMax, 30)-5) }}&nbsp;...
												</el-tag>
											</el-popover>
											<el-tag size="mini" type="primary" v-else>{{ setDefault(itm.options[it], it) }}</el-tag>
										</div>
										<el-tag size="mini" type="info"
											v-if="scope.row[itm.key].length > setDefault(itm.outputTagMax, 5)">
											+{{scope.row[itm.key].length - setDefault(itm.outputTagMax, 5)}}
										</el-tag>
									</div>
									<div v-else-if="itm.outputType=='tag'">
										<span v-if="!scope.row[itm.key]"></span>
										<el-popover placement="right" trigger="hover"
											v-else-if="setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).length>setDefault(itm.outputTextMax, 30)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}
											</span>
											<el-tag size="mini" type="primary" slot="reference">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).slice(0, setDefault(itm.outputTextMax, 30)-5) }}&nbsp;...
											</el-tag>
										</el-popover>
										<el-tag size="mini" type="primary" v-else>{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}</el-tag>
									</div>
									<div v-else-if="itm.multiple">
										<el-popover placement="right" trigger="hover"
											v-if="scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(';').length>setDefault(itm.outputTextMax, 200)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(";") }}
											</span>
											<span slot="reference" style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(";").slice(0, setDefault(itm.outputTextMax, 200)-5) }}&nbsp;...
											</span>
										</el-popover>
										<span v-else style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
											{{ scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(";") }}
										</span>
									</div>
									<div v-else>
										<el-popover placement="right" trigger="hover"
											v-if="setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).length>setDefault(itm.outputTextMax, 200)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}
											</span>
											<span slot="reference" style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).slice(0, setDefault(itm.outputTextMax, 200)-5) }}&nbsp;...
											</span>
										</el-popover>
										<span v-else style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
											{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}
										</span>
									</div>
								</div>
								<div v-else>
									<div v-if="itm.outputType=='tag'">
										<el-popover placement="right" trigger="hover"
											v-if="scope.row[itm.key].length>setDefault(itm.outputTextMax, 30)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key] }}
											</span>
											<el-tag size="mini" type="primary" slot="reference">
												{{ scope.row[itm.key].slice(0, setDefault(itm.outputTextMax, 30)-5) }}&nbsp;...
											</el-tag>
										</el-popover>
										<el-tag size="mini" type="primary" v-else>{{ scope.row[itm.key] }}</el-tag>
									</div>
									<div v-else>
										<el-popover placement="right" trigger="hover"
											v-if="scope.row[itm.key].length>setDefault(itm.outputTextMax, 200)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key] }}
											</span>
											<span slot="reference" style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key].slice(0, setDefault(itm.outputTextMax, 200)-5) }}&nbsp;...
											</span>
										</el-popover>
										<span v-else style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">{{ scope.row[itm.key] }}</span>
									</div>
								</div>
							</template>
						</el-table-column>
						<el-table-column label="错误" v-if="checkable">
							<template slot-scope="scope">
								<span v-if="!Object.keys(scope.row).includes('_tabular_comp_private_log')"
									style="color: gray; white-space: pre-line; word-break: break-all; word-wrap: break-word;">
									未检测
								</span>
								<el-popover placement="right" trigger="hover"
									v-else-if="scope.row['_tabular_comp_private_log'].warn + scope.row['_tabular_comp_private_log'].error > 0">
									<div style="width: 200px; height: 150; font-size: 10px!important; overflow-y:auto;">
										<ol>
											<li v-for="it in scope.row['_tabular_comp_private_log'].info">
												<span v-if="setDefault(it.type, 'error').toLowerCase() === 'warn'"
													style="color: orange; white-space: pre-line; word-break: break-all; word-wrap: break-word;"
													v-text="it.text || it"></span>
												<span v-else
													style="color: red; white-space: pre-line; word-break: break-all; word-wrap: break-word;"
													v-text="it.text || it"></span>
											</li>
										</ol>
									</div>
									<div slot="reference">
										<span v-if="scope.row['_tabular_comp_private_log'].error > 0" style="color: red; white-space: pre-line; word-break: break-all; word-wrap: break-word;"">
											错误{{ scope.row['_tabular_comp_private_log'].error }} 条
										</span>
										&nbsp;&nbsp;
										<span v-if="scope.row['_tabular_comp_private_log'].warn > 0" style="color: orange; white-space: pre-line; word-break: break-all; word-wrap: break-word;">
											警告{{ scope.row['_tabular_comp_private_log'].warn }} 条
										</span>
										</span>
									</div>
								</el-popover>
							</template>
						</el-table-column>
						<el-table-column label="操作" v-if="setDefault(localOperatable, true)">
							<template slot-scope="scope">
								<el-button :icon="scope.row.editable ? 'el-icon-check' : 'el-icon-edit'" type="primary"
									size="mini" circle :plain="scope.row.editable"
									v-if="!setDefault(checkable, false) || !scope.row.editable"
									@click="editLine((currentPage-1)*setDefault(pageSize, 10)+scope.$index)">
								</el-button>
								<el-button icon="el-icon-plus" type="success" size="mini" circle
									@click="addLine((currentPage-1)*setDefault(pageSize, 10)+scope.$index)">
								</el-button>
								<el-button icon="el-icon-delete" type="danger" size="mini" circle
									@click="delLine((currentPage-1)*setDefault(pageSize, 10)+scope.$index)">
								</el-button>
							</template>
						</el-table-column>
					</el-table>
					<el-pagination
						@current-change="handleCurrentChange"
						:current-page="currentPage"
						:page-size="setDefault(pageSize, 10)"
						layout="total, prev, pager, next, jumper"
						:total="showId.length"
						v-if="showId.length > setDefault(pageSize, 10)"
					/>
				</div>
		`,
    data() {
      return {
        showId: [],
        dataShowInfo: [],
        searchBox: {},
        currentPage: 1,
        checkPass: true,
      };
    },
    created() {
      this.searchConfigInit();
    },
    watch: {
      dataLoad(val, new_val) {
        if (this.dataLoad) {
          this.searchConfigInit();
          this.filterSearch();
          this.$emit("update:data-load", false);
        }
      },
    },
    methods: {
      setDefault,
      searchConfigInit() {
        this.colConfig.forEach((itm) => {
          if (this.setDefault(itm.searchable, true)) {
            if (itm.multiple) {
              this.searchBox[itm.key] = [];
            } else if (["select", "switch"].includes(itm.inputType)) {
              this.searchBox[itm.key] = "all";
            } else {
              this.searchBox[itm.key] = "";
            }
          }
        });
      },
      lineInit() {
        let defaultLine = {};
        this.colConfig.forEach((itm) => {
          if (itm.multiple) {
            defaultLine[itm.key] = [];
          } else if (itm.inputType == "select") {
            defaultLine[itm.key] = itm.default || "";
          } else if (itm.inputType == "switch") {
            defaultLine[itm.key] = itm.default || false;
          } else {
            defaultLine[itm.key] = itm.default || "";
          }
        });
        defaultLine.editable = true;
        return defaultLine;
      },
      arrFullIn(a, b) {
        return b.findIndex((itm) => !a.includes(itm)) == -1;
      },
      arrPartialIn(a, b) {
        return b.findIndex((itm) => a.includes(itm)) != -1;
      },
      handleCurrentChange(currentPage) {
        this.currentPage = Math.max(1, currentPage);
      },
      changeValue() {
        this.$forceUpdate();
      },
      editValue(index, key) {
        let tableData = [...this.tableData];
        tableData[this.showId[index]][key] = this.dataShowInfo[index][key];
        this.$emit("data-update", tableData);
      },
      filterSearch() {
        let showId = this.tableData.map((_, k) => k);
        this.colConfig.forEach((itm) => {
          // searchHow = 'fullIn'/'partialIn'/'equal'
          if (
            this.searchBox[itm.key] &&
            this.searchBox[itm.key] !== "all" &&
            (!itm.multiple || this.searchBox[itm.key].length !== 0)
          ) {
            if (itm.multiple && itm.searchHow == "fullIn") {
              showId = showId.filter((infoId) =>
                this.arrFullIn(
                  this.tableData[infoId][itm.key],
                  this.searchBox[itm.key]
                )
              );
            } else if (itm.searchHow == "fullIn") {
              showId = showId.filter((infoId) =>
                this.tableData[infoId][itm.key].includes(
                  this.searchBox[itm.key]
                )
              );
            } else if (itm.multiple && itm.searchHow == "partialIn") {
              showId = showId.filter((infoId) =>
                this.arrPartialIn(
                  this.tableData[infoId][itm.key],
                  this.searchBox[itm.key]
                )
              );
            } else if (itm.multiple) {
              showId = showId.filter(
                (infoId) =>
                  this.tableData[infoId][itm.key].sort().join(";") ==
                  this.searchBox[itm.key].sort().join(";")
              );
            } else {
              showId = showId.filter(
                (infoId) =>
                  this.tableData[infoId][itm.key] == this.searchBox[itm.key]
              );
            }
          }
        });
        this.showId = showId;
        this.dataShowInfo = showId.map((itm) =>
          this.addEditable(this.tableData[itm])
        );
        this.handleCurrentChange(1);
      },
      addEditable(dataLine) {
        let dataLine_ = JSON.parse(JSON.stringify(dataLine));
        dataLine_.editable = dataLine_.editable || false;
        return dataLine_;
      },
      editLine(index) {
        let tableData = [...this.tableData];
        this.dataShowInfo[index].editable = !this.dataShowInfo[index].editable;
        tableData[this.showId[index]].editable =
          this.dataShowInfo[index].editable;
        this.$emit("data-update", tableData);
      },
      addLine(index) {
        let ind = index;
        if (this.showId.length <= index) {
          if (this.showId.length) {
            ind = this.showId.length - 1;
          } else {
            ind = -1;
          }
        }
        let indTrue = -1;
        if (ind !== -1) {
          indTrue = this.showId[ind];
        }
        let tableData = [...this.tableData];
        tableData.splice(indTrue + 1, 0, this.lineInit());
        this.dataShowInfo.splice(ind + 1, 0, this.lineInit());
        this.showId = this.showId.map((_, sId) =>
          sId > ind ? this.showId[sId] + 1 : this.showId[sId]
        );
        this.showId.splice(ind + 1, 0, indTrue + 1);
        this.checkPass = false;
        this.$emit("data-update", tableData);
      },
      delLine(index) {
        let tableData = [...this.tableData];
        tableData.splice(this.dataShowInfo[index], 1);
        this.dataShowInfo.splice(index, 1);
        this.showId = this.showId.map((_, sId) =>
          sId > index ? this.showId[sId] - 1 : this.showId[sId]
        );
        this.showId.splice(index, 1);
        this.$emit("data-update", tableData);
      },
      importData() {
        importFile(
          this,
          setDefault(
            this.importUrl,
            "/ate-tabular-comp/import-data-file-default"
          ),
          this.colConfig,
          (vm, data) => {
						console.log(data.data)
            vm.$emit("data-update", data.data);
            vm.$nextTick(() => {
              vm.searchConfigInit();
              vm.filterSearch();
            });
            if (this.checkable) {
              vm.checkPass = setDefault(data.checkPass, true);
            } else {
              vm.checkPass = true;
            }
          }
        );
      },
      exportData() {
        downloadFile(
          this,
          setDefault(
            this.exportUrl,
            "/ate-tabular-comp/export-data-file-default"
          ),
          this.colConfig,
          this.tableData,
          this.exportFilename
        );
      },
      checkAll() {
        let loading = this.$loading({
          lock: true,
          text: "加载中，请稍候...",
          spinner: "el-icon-loading",
          background: "rgba(0, 10, 0, 0.5)",
        });

        var formData = new FormData();
        formData.append("tableData", JSON.stringify(this.tableData));
        formData.append("colConfig", JSON.stringify(this.colConfig));

        axios
          .post(
            setDefault(
              this.checkUrl,
              "/ate-tabular-comp/check-all-data-default"
            ),
            formData
          )
          .then((response) => {
            this.$emit("data-update", response.data.data);
            this.$nextTick(() => {
              this.searchConfigInit();
              this.filterSearch();
            });
            this.checkPass = setDefault(response.data.checkPass, true);
            if (!this.checkPass) {
              this.$message.warning("存在错误条目");
            } else {
              this.$message.success("所有条目均书写无误");
            }
            loading.close();
          })
          .catch((error) => {
            this.checkPass = false;
            this.searchConfigInit();
            this.filterSearch();
            this.$message.error("条目检查失败");
            loading.close();
          });
      },
      delPage() {
        let tableData = [...this.tableData];
        this.showId
          .slice(
            (this.currentPage - 1) * setDefault(this.pageSize, 10),
            this.currentPage * setDefault(this.pageSize, 10)
          )
          .forEach((ind, count) => {
            let index = ind - count;
            tableData.splice(this.dataShowInfo[index], 1);
            this.dataShowInfo.splice(index, 1);
            this.showId = this.showId.map((_, sId) =>
              sId > index ? this.showId[sId] - 1 : this.showId[sId]
            );
            this.showId.splice(index, 1);
          });
        this.$emit("data-update", tableData);
      },
      clearAll() {
        this.$emit("data-update", []);
        this.$nextTick(() => {
          this.searchConfigInit();
          this.filterSearch();
        });
      },
    },
  });

	Vue.component(
		'ate-tabular-dialog',
		{
			props: [
				"table-data",
				"col-config",
				"data-load",
				"max-height",
				"page-size",
				"edit-rules",
				"edit-inline",
				"global-operatable",
				"local-operatable",
				"importable",
				"import-url",
				"exportable",
				"export-url",
				"export-filename",
			],
			template: `
				<div>
					<el-card shadow="none" v-if="setDefault(globalOperatable, true)">
						<el-col :span="14" style="margin-top: 10px;margin-bottom: 10px;" v-if="setDefault(importable, true)||setDefault(exportable, true)">
							<input type="file" ref="dataFile" accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" v-if="setDefault(importable, true)" />
							<el-button-group>
								<el-button type="success" size="mini" @click="importData" v-if="setDefault(importable, true)">导入条目</el-button>
								<el-button type="warning" size="mini" @click="exportData" v-if="setDefault(exportable, true)">导出条目</el-button>
							</el-button-group>
						</el-col>
						<el-col :span="10" style="margin-top: 10px;margin-bottom: 10px;">
							<el-button-group style="float: right;">
								<el-button type="success" size="mini" @click="addLine(currentPage*setDefault(pageSize, 10)-2)">添加条目</el-button>
								<el-button type="warning" size="mini" @click="delPage">删除本页</el-button>
								<el-button type="danger" size="mini" @click="clearAll">清空条目</el-button>
							</el-button-group>
						</el-col>
					</el-card>
					<el-form :inline="true" :model="searchBox" label-width="100px">
						<el-form-item :label="itm.name" v-for="itm of colConfig" v-if="setDefault(itm.searchable, true)" :key="itm.key">
							<el-input type="number" v-model="searchBox[itm.key]" size="mini"
								:max="itm.max" :min="itm.min" :step="itm.step" :step-strictly="itm.stepstrictly"
								:placeholder="'请输入待查询的'+itm.name"
								clearable @input="e=>changeValue()"
								v-if="setDefault(itm.inputType, 'input') == 'input-number'">
							</el-input>
							<el-input v-model="searchBox[itm.key]" size="mini"
								:placeholder="'请输入待查询的'+itm.name"
								clearable @input="e=>changeValue()"
								v-else-if="setDefault(itm.inputType, 'input') == 'input'">
							</el-input>
							<el-select v-model="searchBox[itm.key]" size="mini" :multiple="itm.multiple" filterable
								:clearable="itm.multiple"
								:placeholder="'请输入待查询的'+itm.name"
								@change="e=>changeValue()"
								v-if="itm.inputType == 'select'">
								<el-option label="显示全部" value="all" v-if="!itm.multiple"></el-option>
								<el-option v-for="label, key in itm.options" :key="key"
										:label="label" :value="key">
								</el-option>
							</el-select>
							<el-select v-model="searchBox[itm.key]" size="mini" :multiple="itm.multiple" filterable
								:placeholder="'请输入待查询的'+itm.name"
								@change="e=>changeValue()"
								v-if="itm.inputType == 'switch'">
								<el-option label="显示全部" value="all"></el-option>
								<el-option :label="setDefault(itm.trueLabel, '显示勾选项')" :value="true"></el-option>
								<el-option :label="setDefault(itm.falseLabel, '显示未勾选项')" :value="false"></el-option>
							</el-select>
						</el-form-item>
						<el-form-item>
							<el-button type="primary" size="mini" @click="filterSearch">筛选</el-button>
						</el-form-item>
					</el-form>
					<el-table :data="dataShowInfo.slice((currentPage-1)*setDefault(pageSize, 10),currentPage*setDefault(pageSize, 10))" size="small"
						:max-height="setDefault(maxHeight, 300)">
						<el-table-column label="序号" :show-overflow-tooltip="true" :width="120">
							<template slot-scope="scope">
								<span>{{ showId[(currentPage-1)*setDefault(pageSize, 10)+scope.$index]+1 }}</span>
							</template>
						</el-table-column>
						<el-table-column :label="itm.name" :show-overflow-tooltip="true"
							v-for="itm of colConfig" :key="itm.key">
							<template slot-scope="scope">
								<el-switch v-model="scope.row[itm.key]" size="mini"
									:active-color="setDefault(itm.activeColor, '#13ce66')"
									:inactive-color="setDefault(itm.activeColor, '#ff4949')"
									v-if="itm.inputType == 'switch'"
									@change="e=>editValue((currentPage-1)*setDefault(pageSize, 10)+scope.$index, itm.key)">
								</el-switch>
								<div v-else-if="itm.inputType == 'select'">
									<div v-if="itm.outputType=='tag' && itm.multiple">
										<div v-for="it of scope.row[itm.key].slice(0, setDefault(itm.outputTagMax, 5))" :key="it">
											<span v-if="!it"></span>
											<el-popover placement="right" trigger="hover"
												v-else-if="setDefault(itm.options[it], it).length>setDefault(itm.outputTextMax, 30)">
												<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
															white-space: pre-line; word-break: break-all; word-wrap: break-word;">
													{{ setDefault(itm.options[it], it) }}
												</span>
												<el-tag size="mini" type="primary" slot="reference">
													{{ setDefault(itm.options[it], it).slice(0, setDefault(itm.outputTextMax, 30)-5) }}&nbsp;...
												</el-tag>
											</el-popover>
											<el-tag size="mini" type="primary" v-else>{{ setDefault(itm.options[it], it) }}</el-tag>
										</div>
										<el-tag size="mini" type="info"
											v-if="scope.row[itm.key].length > setDefault(itm.outputTagMax, 5)">
											+{{scope.row[itm.key].length - setDefault(itm.outputTagMax, 5)}}
										</el-tag>
									</div>
									<div v-else-if="itm.outputType=='tag'">
										<span v-if="!scope.row[itm.key]"></span>
										<el-popover placement="right" trigger="hover"
											v-else-if="setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).length>setDefault(itm.outputTextMax, 30)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}
											</span>
											<el-tag size="mini" type="primary" slot="reference">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).slice(0, setDefault(itm.outputTextMax, 30)-5) }}&nbsp;...
											</el-tag>
										</el-popover>
										<el-tag size="mini" type="primary" v-else>{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}</el-tag>
									</div>
									<div v-else-if="itm.multiple">
										<el-popover placement="right" trigger="hover"
											v-if="scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(';').length>setDefault(itm.outputTextMax, 200)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(";") }}
											</span>
											<span slot="reference" style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(";").slice(0, setDefault(itm.outputTextMax, 200)-5) }}&nbsp;...
											</span>
										</el-popover>
										<span v-else  style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
											{{ scope.row[itm.key].map(it=>setDefault(itm.options[it], it)).join(";") }}
										</span>
									</div>
									<div v-else>
										<el-popover placement="right" trigger="hover"
											v-if="setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).length>setDefault(itm.outputTextMax, 200)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}
											</span>
											<span slot="reference" style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]).slice(0, setDefault(itm.outputTextMax, 200)-5) }}&nbsp;...
											</span>
										</el-popover>
										<span v-else style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
											{{ setDefault(itm.options[scope.row[itm.key]], scope.row[itm.key]) }}
										</span>
									</div>
								</div>
								<div v-else>
									<div v-if="itm.outputType=='tag'">
										<el-popover placement="right" trigger="hover"
											v-if="scope.row[itm.key].length>setDefault(itm.outputTextMax, 30)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key] }}
											</span>
											<el-tag size="mini" type="primary" slot="reference">
												{{ scope.row[itm.key].slice(0, setDefault(itm.outputTextMax, 30)-5) }}&nbsp;...
											</el-tag>
										</el-popover>
										<el-tag size="mini" type="primary" v-else>{{ scope.row[itm.key] }}</el-tag>
									</div>
									<div v-else>
										<el-popover placement="right" trigger="hover"
											v-if="scope.row[itm.key].length>setDefault(itm.outputTextMax, 200)">
											<span style="width: 50px; height: 30px; font-size: 10px!important; overflow-y:auto;
														white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key] }}
											</span>
											<span slot="reference" style="white-space: pre-line; word-break: break-all; word-wrap: break-word;">
												{{ scope.row[itm.key].slice(0, setDefault(itm.outputTextMax, 200)-5) }}&nbsp;...
											</span>
										</el-popover>
										<span v-else>{{ scope.row[itm.key] }}</span>
									</div>
								</div>
							</template>
						</el-table-column>
						<el-table-column label="操作"  v-if="setDefault(localOperatable, true)">
							<template slot-scope="scope">
								<el-button icon="el-icon-edit" type="primary"
									size="mini" circle :plain="scope.row.editable"
									@click="editLine((currentPage-1)*setDefault(pageSize, 10)+scope.$index)">
								</el-button>
								<el-button icon="el-icon-plus" type="success" size="mini" circle
									@click="addLine((currentPage-1)*setDefault(pageSize, 10)+scope.$index)">
								</el-button>
								<el-button icon="el-icon-delete" type="danger" size="mini" circle
									@click="delLine((currentPage-1)*setDefault(pageSize, 10)+scope.$index)">
								</el-button>
							</template>
						</el-table-column>
					</el-table>
					<el-pagination  @current-change="handleCurrentChange"
									:current-page="currentPage"
									:page-size="setDefault(pageSize, 10)"
									layout="total, prev, pager, next, jumper"
									:total="showId.length"
									v-if="showId.length>setDefault(pageSize, 10)">
					</el-pagination>
					<el-dialog :title="'编辑条目['+editBox.trueIndex+']属性'" width="60%" :visible.sync="dialogVisible">
						<el-form :inline="setDefault(editInline, false)" :model="editBox"
							label-width="100px" :rules="setDefault(editRules, {})" ref="innerEditDialog">
							<el-form-item :label="itm.name" v-for="itm of colConfig" v-if="itm.inputType !== 'switch'" :key="itm.key">
								<el-input type="number" v-model="editBox[itm.key]" size="mini" :placeholder="itm.placeholder"
									:max="itm.max" :min="itm.min" :step="itm.step" :step-strictly="itm.stepstrictly"
									v-if="itm.inputType == 'input-number'"
									@input="e=>changeValue()"></el-input>
								<el-input v-model="editBox[itm.key]" size="mini" :placeholder="itm.placeholder"
									v-else-if="setDefault(itm.inputType, 'input') == 'input'"
									@input="e=>changeValue()"></el-input>
								<el-select v-model="editBox[itm.key]" size="mini" :placeholder="itm.placeholder"
									:multiple="itm.multiple" filterable
									v-else-if="itm.inputType == 'select'"
									@change="e=>changeValue()">
									<el-option v-for="label, key in itm.options" :key="key"
											:label="label" :value="key">
									</el-option>
								</el-select>
							</el-form-item>
							<el-form-item style="float: right;">
								<el-button type="primary" size="mini" @click="confirmEdit">提交</el-button>
								<el-button type="primary" size="mini" plain @click="dialogVisible=false;">取消</el-button>
							</el-form-item>
						</el-form>
					</el-dialog>
				</div>
			`,
			data() {
				return {
					showId: [],
					dataShowInfo: [],
					searchBox : {},
					editBox: {},
					currentPage: 1,
					dialogVisible: false,
				}
			},
			created(){
				this.searchConfigInit();
				this.clearEditBox();
			},
			watch: {
				dataLoad(val, new_val){
					if (this.dataLoad){
						this.searchConfigInit();
						this.filterSearch();
						this.$emit('update:data-load', false);
					}
				}
			},
			methods: {
				setDefault,
				searchConfigInit(){
					this.colConfig.forEach(itm=>{
						if (this.setDefault(itm.searchable, true)){
							if (itm.multiple){
								this.searchBox[itm.key] = [];
							}else if(['select', 'switch'].includes(itm.inputType)){
								this.searchBox[itm.key] = 'all';
							}else{
								this.searchBox[itm.key] = '';
							}
						}
					})
				},
				clearEditBox(ind, indTrue){
					let defaultLine = {index: ind, trueIndex: indTrue, isNew: true};
					this.colConfig.forEach(itm=>{
						if (itm.multiple){
							defaultLine[itm.key] = [];
						}else if(itm.inputType == 'select'){
							defaultLine[itm.key] = itm.default || '';
						}else if(itm.inputType == 'switch'){
							defaultLine[itm.key] = itm.default || false;
						}else{
							defaultLine[itm.key] = itm.default || '';
						}
					})
					this.editBox = defaultLine;
				},
				lineInit(){
					let defaultLine = {};
					this.colConfig.forEach(itm=>{
						if (itm.multiple){
							defaultLine[itm.key] = [];
						}else if(itm.inputType == 'select'){
							defaultLine[itm.key] = itm.default || '';
						}else if(itm.inputType == 'switch'){
							defaultLine[itm.key] = itm.default || false;
						}else{
							defaultLine[itm.key] = itm.default || '';
						}
					})
					defaultLine.editable = true;
					return defaultLine
				},
				arrFullIn(a,b){
					return b.findIndex(itm => !a.includes(itm)) == -1;
				},
				arrPartialIn(a,b){
					return b.findIndex(itm => a.includes(itm)) != -1;
				},
				handleCurrentChange(currentPage){
					this.currentPage = Math.max(1, currentPage);
				},
				changeValue(){
					this.$forceUpdate();
				},
				editValue(index, key){
					let tableData = [...this.tableData];
					tableData[this.showId[index]][key] = this.dataShowInfo[index][key];
					this.$emit("data-update", tableData);
				},
				filterSearch(){
					let showId = this.tableData.map((_,k)=>k);
					this.colConfig.forEach(itm=>{
						// searchHow = 'fullIn'/'partialIn'/'equal'
						if (this.searchBox[itm.key] && this.searchBox[itm.key] !== 'all' && (!itm.multiple || this.searchBox[itm.key].length !== 0)){
							if (itm.multiple && itm.searchHow == 'fullIn'){
								showId = showId.filter(infoId => this.arrFullIn(this.tableData[infoId][itm.key], this.searchBox[itm.key]));
							}else if (itm.searchHow == 'fullIn'){
								showId = showId.filter(infoId => this.tableData[infoId][itm.key].includes(this.searchBox[itm.key]));
							}else if (itm.multiple && itm.searchHow == 'partialIn'){
								showId = showId.filter(infoId => this.arrPartialIn(this.tableData[infoId][itm.key], this.searchBox[itm.key]));
							}else if (itm.multiple){
								showId = showId.filter(infoId => this.tableData[infoId][itm.key].sort().join(';')==this.searchBox[itm.key].sort().join(';'));
							}else{
								showId = showId.filter(infoId => this.tableData[infoId][itm.key]==this.searchBox[itm.key]);
							}
						}
					})
					this.showId = showId;
					this.dataShowInfo = showId.map(itm => this.tableData[itm]);
					this.handleCurrentChange(1);
				},
				editLine(ind){
					let defaultLine = {index: ind, trueIndex: this.showId[ind], isNew: false};
					this.colConfig.forEach(itm=>{
						defaultLine[itm.key] = this.dataShowInfo[ind][itm.key];
					})
					this.editBox = defaultLine;
					this.dialogVisible = true;
				},
				addLine(index){
					let ind = index;
					if(this.showId.length <= index){
						if (this.showId.length){
							ind = this.showId.length - 1;
						}else{
							ind = -1;
						}
					}
					let indTrue = -1;
					if (ind !== -1){
						indTrue = this.showId[ind];
					}
					this.clearEditBox(ind + 1, indTrue + 1);
					this.dialogVisible = true;
				},
				confirmEdit(){
					this.$refs.innerEditDialog.validate((valid)=>{
						if(valid){
							let tableData = [...this.tableData];
							if (this.editBox.isNew){
								tableData.splice(this.editBox.trueIndex, 0, this.editBox);
								this.dataShowInfo.splice(this.editBox.index, 0, this.editBox);
								this.showId = this.showId.map((_, sId)=> sId > ind ? this.showId[sId] + 1 : this.showId[sId])
								this.showId.splice(this.editBox.index, 0, this.editBox.trueIndex)
							} else {
								tableData.splice(this.editBox.trueIndex, 1, this.editBox);
								this.dataShowInfo.splice(this.editBox.index, 1, this.editBox);
								this.showId.splice(this.editBox.index, 1, this.editBox.trueIndex)
							}
							this.$emit("data-update", tableData);
							this.dialogVisible = false;
							this.clearEditBox();
						}else{
							this.$message.warning("条目编辑有误！")
						}
					})

				},
				delLine(index){
					let tableData = [...this.tableData];
					tableData.splice(this.dataShowInfo[index], 1);
					this.dataShowInfo.splice(index, 1);
					this.showId = this.showId.map((_, sId)=> sId > index ? this.showId[sId] - 1 : this.showId[sId]);
					this.showId.splice(index, 1);
					this.$emit("data-update", tableData);
				},

				importData(){
					importFile(this, setDefault(this.importUrl, "/ate-tabular-comp/import-data-file-default"), this.colConfig, (vm, data)=>{
						vm.$emit("data-update", data.data);
						vm.$nextTick(()=>{
							vm.searchConfigInit();
							vm.filterSearch();
						})
					})
				},
				exportData(){
					downloadFile(this, setDefault(this.exportUrl, "/ate-tabular-comp/export-data-file-default"), this.colConfig, this.tableData, this.exportFilename);
				},
				delPage(){
					let tableData = [...this.tableData];
					this.showId.slice((this.currentPage-1)*setDefault(this.pageSize, 10), this.currentPage*setDefault(this.pageSize, 10)).forEach((ind, count)=>{
						let index = ind - count;
						tableData.splice(this.dataShowInfo[index], 1);
						this.dataShowInfo.splice(index, 1);
						this.showId = this.showId.map((_, sId)=> sId > index ? this.showId[sId] - 1 : this.showId[sId]);
						this.showId.splice(index, 1);
					})
					this.$emit("data-update", tableData);
				},
				clearAll(){
					this.$emit("data-update", []);
					this.$nextTick(()=>{
						this.searchConfigInit();
						this.filterSearch();
					})
				}
			}
		});
}